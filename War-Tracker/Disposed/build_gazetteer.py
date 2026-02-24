import os
import pandas as pd
from sqlalchemy import text
from app import create_app
from extensions import db


class SyriaLocation(db.Model):
    __tablename__ = "syria_gazetteer"

    id = db.Column(db.Integer, primary_key=True)

    # Core names
    name_en = db.Column(db.String(200), index=True, nullable=False)
    name_ar = db.Column(db.String(200), index=True, default="")

    # Useful metadata
    admin_level = db.Column(db.String(50), index=True)      # e.g. sheet name or ADM level
    parent_gov = db.Column(db.String(120), index=True, default="")  # governorate/admin1 if available

    # New helpful fields (since you drop/create, this is safe)
    pcode = db.Column(db.String(40), index=True)            # any pcode for the row
    source_sheet = db.Column(db.String(60), index=True)     # which sheet it came from
    used_fallback = db.Column(db.Boolean, default=False)    # coords came from parent center?

    # Coords
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)


def normalize_col(col: str) -> str:
    return str(col).strip().lower().replace("\n", " ").replace("\r", " ")


def find_column(df: pd.DataFrame, possible_names: list[str]):
    """
    Finds a column using aggressive substring matching:
    - exact match after normalization
    - substring match after normalization
    """
    norm_cols = {c: normalize_col(c) for c in df.columns}
    for col, ncol in norm_cols.items():
        for name in possible_names:
            n = normalize_col(name)
            if n == ncol or n in ncol:
                return col
    return None


def safe_str(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)) or pd.isna(v):
        return ""
    return str(v).strip()


def safe_float(v):
    if v is None or pd.isna(v):
        return None
    try:
        return float(v)
    except Exception:
        return None


def clean_name(name: str) -> str:
    n = safe_str(name).strip()
    if not n:
        return ""
    n = n.lower()
    # Keep your old cleaning + a bit more
    for suffix in [" sub-district", " district", " subdistrict", " governorate"]:
        n = n.replace(suffix, "")
    return n.strip()


def load_centers(xl: pd.ExcelFile, file_path: str):
    """
    Build center lookup dicts:
      adm3_centers[pcode] = (lat,lng)
      adm2_centers[pcode] = (lat,lng)
      adm1_centers[pcode] = (lat,lng)
    Uses the "best available" columns in each sheet.
    """
    adm1 = {}
    adm2 = {}
    adm3 = {}

    def build_center_map(sheet_name: str, level: str, out_dict: dict):
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df.columns = [str(c).strip() for c in df.columns]

        c_pcode = find_column(df, ["pcode", "adm1_pcode", "adm2_pcode", "adm3_pcode", "admin_pcode"])
        c_lat = find_column(df, ["center_lat", "y_coord", "latitude", "lat", "point_y"])
        c_lng = find_column(df, ["center_lon", "x_coord", "longitude", "lng", "lon", "point_x"])

        if not (c_pcode and c_lat and c_lng):
            return 0

        count = 0
        for _, r in df.iterrows():
            p = safe_str(r.get(c_pcode))
            if not p:
                continue
            lat = safe_float(r.get(c_lat))
            lng = safe_float(r.get(c_lng))
            if lat is None or lng is None:
                continue
            out_dict[p] = (lat, lng)
            count += 1
        return count

    # Common UN OCHA sheet names in these workbooks
    sheet_names = set(xl.sheet_names)

    # Try admin1/admin2/admin3 first (if present)
    if "syr_admin1" in sheet_names:
        build_center_map("syr_admin1", "ADM1", adm1)
    if "syr_admin2" in sheet_names:
        build_center_map("syr_admin2", "ADM2", adm2)
    if "syr_admin3" in sheet_names:
        build_center_map("syr_admin3", "ADM3", adm3)

    # Some workbooks also have admin points with coords per admin area
    # If it contains pcodes, this can augment center maps.
    if "syr_adminpoints" in sheet_names:
        df = pd.read_excel(file_path, sheet_name="syr_adminpoints")
        df.columns = [str(c).strip() for c in df.columns]

        # coords
        c_lat = find_column(df, ["y_coord", "center_lat", "latitude", "lat", "point_y"])
        c_lng = find_column(df, ["x_coord", "center_lon", "longitude", "lng", "lon", "point_x"])

        # pcodes for multiple levels (try them all)
        c_adm3 = find_column(df, ["adm3_pcode", "adm3_pcod", "adm3pcode"])
        c_adm2 = find_column(df, ["adm2_pcode", "adm2_pcod", "adm2pcode"])
        c_adm1 = find_column(df, ["adm1_pcode", "adm1_pcod", "adm1pcode"])

        if c_lat and c_lng:
            for _, r in df.iterrows():
                lat = safe_float(r.get(c_lat))
                lng = safe_float(r.get(c_lng))
                if lat is None or lng is None:
                    continue

                p3 = safe_str(r.get(c_adm3)) if c_adm3 else ""
                p2 = safe_str(r.get(c_adm2)) if c_adm2 else ""
                p1 = safe_str(r.get(c_adm1)) if c_adm1 else ""

                if p3 and p3 not in adm3:
                    adm3[p3] = (lat, lng)
                if p2 and p2 not in adm2:
                    adm2[p2] = (lat, lng)
                if p1 and p1 not in adm1:
                    adm1[p1] = (lat, lng)

    return adm1, adm2, adm3


def resolve_fallback_coords(row, adm1, adm2, adm3):
    """
    Neighborhoods often have:
      adm3_pcode, adm2_pcode, adm1_pcode
    Try ADM3 → ADM2 → ADM1 center.
    """
    p3 = safe_str(row.get("adm3_pcode"))
    p2 = safe_str(row.get("adm2_pcode"))
    p1 = safe_str(row.get("adm1_pcode"))

    if p3 and p3 in adm3:
        return adm3[p3]
    if p2 and p2 in adm2:
        return adm2[p2]
    if p1 and p1 in adm1:
        return adm1[p1]
    return None


def build():
    app = create_app()
    with app.app_context():
        print("🚀 Starting Gazetteer Build (Total Read + Fallback Coords)...")

        db.session.execute(text("DROP TABLE IF EXISTS syria_gazetteer"))
        db.create_all()

        file_path = "syr_admin.xlsx"
        if not os.path.exists(file_path):
            print(f"❌ Error: {file_path} not found!")
            return

        xl = pd.ExcelFile(file_path)

        # Load centers once for fallback use
        adm1_centers, adm2_centers, adm3_centers = load_centers(xl, file_path)
        print(f"🧭 Center lookups loaded: ADM3={len(adm3_centers)}, ADM2={len(adm2_centers)}, ADM1={len(adm1_centers)}\n")

        summary = []
        total_imported = 0

        # Heuristics for columns across different sheets
        NAME_EN_CANDIDATES = [
            "neighborhoodname_en", "featurename_en", "adm4_en", "adm3_name", "adm2_name", "adm1_name",
            "name_en", "name"
        ]
        NAME_AR_CANDIDATES = [
            "neighborhoodname_ar", "featurename_ar", "adm4_ar", "adm3_name1", "adm2_name1", "adm1_name1",
            "name_ar"
        ]
        GOV_CANDIDATES = ["adm1_name", "adm1_en", "governorate_name_en", "admin1name_en"]

        LAT_CANDIDATES = ["center_lat", "y_coord", "latitude", "lat", "point_y"]
        LNG_CANDIDATES = ["center_lon", "x_coord", "longitude", "lng", "lon", "point_x"]

        PCODE_CANDIDATES = ["pcode", "neighborhoodpcode", "adm4_pcode", "adm3_pcode", "adm2_pcode", "adm1_pcode"]

        for sheet_name in xl.sheet_names:
            print(f"📖 Scanning Sheet: {sheet_name}")

            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            except Exception as e:
                print(f"   ❌ Failed to read {sheet_name}: {e}")
                continue

            df.columns = [str(c).strip() for c in df.columns]

            c_en = find_column(df, NAME_EN_CANDIDATES)
            c_ar = find_column(df, NAME_AR_CANDIDATES)
            c_gov = find_column(df, GOV_CANDIDATES)
            c_lat = find_column(df, LAT_CANDIDATES)
            c_lng = find_column(df, LNG_CANDIDATES)
            c_pcode = find_column(df, PCODE_CANDIDATES)

            # Stats
            rows = len(df)
            imported = 0
            missing_name = 0
            missing_coords = 0
            errors = 0
            fallback_used = 0

            # If no name column, skip sheet
            if not c_en:
                print(f"   ⚠️ No name_en-like column found. Skipping.")
                continue

            # If no coords, we may still import via fallback for neighborhoods-style sheets
            has_direct_coords = bool(c_lat and c_lng)

            if has_direct_coords:
                print(f"   ✅ name_en='{c_en}' | coords='{c_lat}, {c_lng}'")
            else:
                print(f"   ⚠️ No direct coords in {sheet_name}. Will use fallback if possible.")
                # Only makes sense if it has adm*_pcode columns
                if not all(x in df.columns for x in ["adm3_pcode", "adm2_pcode", "adm1_pcode"]):
                    print(f"   ⚠️ No fallback path available (missing adm*_pcode). Skipping.")
                    continue
                print("   ↪ Using parent admin center (ADM3→ADM2→ADM1) via *_pcode columns.")

            # Build row objects in memory then bulk insert (faster)
            objs = []

            for _, row in df.iterrows():
                try:
                    raw_name = row.get(c_en)
                    name = clean_name(raw_name)
                    if not name:
                        missing_name += 1
                        continue

                    # Resolve coordinates
                    used_fb = False
                    lat = None
                    lng = None

                    if has_direct_coords:
                        lat = safe_float(row.get(c_lat))
                        lng = safe_float(row.get(c_lng))
                    else:
                        # fallback lookup uses the literal columns adm3_pcode/adm2_pcode/adm1_pcode
                        coords = resolve_fallback_coords(row, adm1_centers, adm2_centers, adm3_centers)
                        if coords:
                            lat, lng = coords
                            used_fb = True

                    if lat is None or lng is None:
                        missing_coords += 1
                        continue

                    gov = safe_str(row.get(c_gov)) if c_gov else ""
                    name_ar = safe_str(row.get(c_ar)) if c_ar else ""
                    pcode = safe_str(row.get(c_pcode)) if c_pcode else ""

                    obj = SyriaLocation(
                        name_en=name,
                        name_ar=name_ar,
                        admin_level=sheet_name,
                        parent_gov=gov,
                        pcode=pcode,
                        source_sheet=sheet_name,
                        used_fallback=used_fb,
                        lat=lat,
                        lng=lng,
                    )
                    objs.append(obj)
                    imported += 1
                    if used_fb:
                        fallback_used += 1

                except Exception:
                    errors += 1
                    continue

            if objs:
                # bulk insert for speed
                db.session.bulk_save_objects(objs)
                db.session.commit()

            total_imported += imported
            print(
                f"   📥 Imported {imported} / {rows} "
                f"(missing_name={missing_name}, missing_coords={missing_coords}, errors={errors}, fallback_used={fallback_used})\n"
            )

            summary.append(
                (sheet_name, rows, imported, missing_name, missing_coords, errors, fallback_used)
            )

        print("✅ GAZETTEER COMPLETE")
        print(f"   Total imported locations: {total_imported}\n")

        print("📊 Sheet Summary")
        for (sheet, rows, imp, mn, mc, err, fb) in summary:
            # align output similar to your last run
            print(
                f" - {sheet:<18} rows={rows:>6}  imported={imp:>6}  "
                f"miss_name={mn:>6}  miss_coords={mc:>6}  errors={err:>6}  fallback={fb:>6}"
            )


if __name__ == "__main__":
    build()
