"""
Syria Civil War Simulation Data (2011-2013)
============================================
Each entry defines:
  - date: when the event happened
  - headline: news headline
  - location: place name (must match data_locations.py or syria_data.py)
  - lat/lng: explicit coords (fallback if geocoder misses)
  - controller_before: who held it before
  - controller_after: who holds it after this event
  - importance: 1-10 (affects influence radius on map)
  - category: event type for map icons

Controller values must match FACTION_COLORS in war.html:
  "Government Control", "Rebel Control", "ISIS Control", "SDF Control", "Neutral"
"""

SIMULATION_EVENTS = [
    # =========================================================================
    # 2011: THE UPRISING — Mostly government control, first cracks appear
    # =========================================================================
    {
        "date": "2011-03-15",
        "headline": "Protests erupt in Daraa calling for freedom",
        "location": "Daraa",
        "lat": 32.6184, "lng": 36.1014,
        "controller_before": "Government Control",
        "controller_after": "Government Control",  # Still gov, just protests
        "importance": 8,
        "category": "protest"
    },
    {
        "date": "2011-04-25",
        "headline": "Syrian Army tanks storm Daraa to crush protests",
        "location": "Daraa",
        "lat": 32.6184, "lng": 36.1014,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 8,
        "category": "battle"
    },
    {
        "date": "2011-06-06",
        "headline": "120 security forces killed in Jisr al-Shughur ambush",
        "location": "Jisr al-Shughur",
        "lat": 35.8136, "lng": 36.3219,
        "controller_before": "Government Control",
        "controller_after": "Government Control",  # Gov retains but shaken
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2011-07-29",
        "headline": "Defecting officers announce formation of Free Syrian Army",
        "location": "Homs",
        "lat": 34.7324, "lng": 36.7137,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 9,
        "category": "political"
    },
    {
        "date": "2011-09-27",
        "headline": "Government forces retake Rastan after days of fighting",
        "location": "Rastan",
        "lat": 34.9264, "lng": 36.7336,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2011-11-16",
        "headline": "FSA rebels attack Air Force Intelligence base in Harasta",
        "location": "Harasta",
        "lat": 33.5583, "lng": 36.3667,
        "controller_before": "Government Control",
        "controller_after": "Government Control",  # Attack but gov holds
        "importance": 5,
        "category": "battle"
    },

    # =========================================================================
    # 2012: THE REBEL ADVANCE — Green starts appearing across the map
    # =========================================================================
    {
        "date": "2012-01-21",
        "headline": "Free Syrian Army captures the town of Zabadani near Lebanon border",
        "location": "Zabadani",
        "lat": 33.7250, "lng": 36.0972,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2012-02-04",
        "headline": "Government forces launch massive offensive on Homs district of Baba Amr",
        "location": "Baba Amr",
        "lat": 34.7100, "lng": 36.6900,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Still rebel during siege
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-03-01",
        "headline": "Syrian Army recaptures Baba Amr in Homs from rebels",
        "location": "Baba Amr",
        "lat": 34.7100, "lng": 36.6900,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-06-12",
        "headline": "Rebels seize control of Al-Haffah in Latakia province",
        "location": "Al-Haffah",
        "lat": 35.5500, "lng": 36.0833,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 4,
        "category": "battle"
    },
    {
        "date": "2012-07-19",
        "headline": "Rebels capture the Bab al-Hawa border crossing with Turkey",
        "location": "Bab al-Hawa",
        "lat": 36.2439, "lng": 36.6531,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-07-20",
        "headline": "Rebels seize the Bab al-Salam border crossing north of Aleppo",
        "location": "Bab al-Salam",
        "lat": 36.6283, "lng": 37.0833,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-07-22",
        "headline": "Opposition fighters take control of Jarablus on Turkish border",
        "location": "Jarablus",
        "lat": 36.8167, "lng": 38.0111,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2012-07-23",
        "headline": "FSA announces liberation of Al-Bab city in Aleppo province",
        "location": "Bab",
        "lat": 36.3667, "lng": 37.5167,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-07-25",
        "headline": "Rebels storm Aleppo city, taking control of Sakhour and Hanano districts",
        "location": "Masaken Hanano",
        "lat": 36.2333, "lng": 37.1900,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 8,
        "category": "battle"
    },
    {
        "date": "2012-07-28",
        "headline": "Government forces repel rebel attack on Aleppo Citadel",
        "location": "Aleppo",
        "lat": 36.2021, "lng": 37.1343,
        "controller_before": "Government Control",
        "controller_after": "Government Control",  # Gov holds citadel
        "importance": 9,
        "category": "battle"
    },
    {
        "date": "2012-08-25",
        "headline": "Rebels capture the town of Ariha in Idlib",
        "location": "Ariha",
        "lat": 35.8167, "lng": 36.6167,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2012-10-09",
        "headline": "FSA fighters seize strategic town of Maarrat al-Nu'man on Damascus-Aleppo highway",
        "location": "Maarat al-Numan",
        "lat": 35.6461, "lng": 36.6769,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-11-18",
        "headline": "Rebels capture Base 46 near Aleppo after weeks of siege",
        "location": "Base 46",
        "lat": 36.3833, "lng": 36.8833,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-12-11",
        "headline": "Opposition forces take control of Sheikh Suleiman base",
        "location": "Sheikh Suleiman",
        "lat": 36.3333, "lng": 36.9500,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },

    # Additional 2012 rebel gains to fill the map  
    {
        "date": "2012-03-15",
        "headline": "Rebels establish control over parts of Idlib city",
        "location": "Idlib",
        "lat": 35.9306, "lng": 36.6339,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 8,
        "category": "battle"
    },
    {
        "date": "2012-05-10",
        "headline": "FSA takes control of Saraqib in Idlib province",
        "location": "Saraqib",
        "lat": 35.8636, "lng": 36.8053,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-05-20",
        "headline": "Rebels seize Binnish town in northern Idlib",
        "location": "Binnish",
        "lat": 35.9569, "lng": 36.7136,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 4,
        "category": "battle"
    },
    {
        "date": "2012-06-01",
        "headline": "FSA captures Taftanaz military airbase area",
        "location": "Taftanaz",
        "lat": 35.9833, "lng": 36.7833,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-08-10",
        "headline": "Rebels take Azaz in northern Aleppo countryside",
        "location": "Azaz",
        "lat": 36.5833, "lng": 37.0500,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-09-05",
        "headline": "FSA captures Manbij city in eastern Aleppo",
        "location": "Manbij",
        "lat": 36.5333, "lng": 37.9500,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-09-20",
        "headline": "Rebels take Kafr Nabl in southern Idlib",
        "location": "Kafr Nabl",
        "lat": 35.6000, "lng": 36.5500,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 4,
        "category": "battle"
    },
    {
        "date": "2012-11-01",
        "headline": "Rebels capture Khan Shaykhun on M5 highway",
        "location": "Khan Shaykhun",
        "lat": 35.4333, "lng": 36.6500,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-09-28",
        "headline": "Rebels seize Tal Abyad border crossing with Turkey",
        "location": "Tal Abyad",
        "lat": 36.6969, "lng": 38.9567,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-11-08",
        "headline": "Rebels capture Ras al-Ain in Hasakah province",
        "location": "Ras al-Ain",
        "lat": 36.8500, "lng": 40.0667,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },

    # Government holds in the south and coast
    {
        "date": "2012-04-12",
        "headline": "Government reinforces Damascus suburbs, secures Douma perimeter",
        "location": "Douma",
        "lat": 33.5714, "lng": 36.4014,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-06-20",
        "headline": "Syrian Army maintains control of Latakia city",
        "location": "Latakia",
        "lat": 35.5317, "lng": 35.7901,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 8,
        "category": "battle"
    },
    {
        "date": "2012-08-01",
        "headline": "Government forces hold Tartus naval base and city",
        "location": "Tartus",
        "lat": 34.8890, "lng": 35.8866,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 8,
        "category": "military"
    },

    # =========================================================================
    # 2013: GOVERNMENT COUNTER-ATTACK + ISIS EMERGES — Red fights back, Black appears
    # =========================================================================
    {
        "date": "2013-01-11",
        "headline": "Rebels capture Taftanaz Air Base in Idlib",
        "location": "Taftanaz",
        "lat": 35.9833, "lng": 36.7833,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Already rebel, reinforcing
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-03-04",
        "headline": "Rebels overrun Raqqa, the first provincial capital to fall",
        "location": "Raqqa",
        "lat": 35.9524, "lng": 39.0120,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 9,
        "category": "battle"
    },
    {
        "date": "2013-03-23",
        "headline": "Rebels seize the 38th Division base near Saida in Daraa",
        "location": "Daraa",
        "lat": 32.6184, "lng": 36.1014,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-03-25",
        "headline": "Rebels capture Nawa in western Daraa countryside",
        "location": "Nawa",
        "lat": 32.8667, "lng": 36.0333,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-03-28",
        "headline": "FSA takes Jasim in Daraa province",
        "location": "Jasim",
        "lat": 32.9667, "lng": 36.0667,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 4,
        "category": "battle"
    },
    {
        "date": "2013-04-03",
        "headline": "Rebels capture Inkhil south of Damascus",
        "location": "Inkhil",
        "lat": 33.0167, "lng": 36.1167,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 4,
        "category": "battle"
    },
    {
        "date": "2013-04-05",
        "headline": "Syrian Army breaks siege of Wadi Deif base in Idlib",
        "location": "Wadi al-Deif",
        "lat": 35.6333, "lng": 36.6667,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-04-24",
        "headline": "Minaret of Umayyad Mosque in Aleppo destroyed during clashes",
        "location": "Aleppo",
        "lat": 36.2021, "lng": 37.1343,
        "controller_before": "Government Control",
        "controller_after": "Government Control",  # Gov holds old city area
        "importance": 8,
        "category": "battle"
    },
    {
        "date": "2013-05-19",
        "headline": "Syrian Army and Hezbollah launch offensive to retake Al-Qusayr",
        "location": "Qusayr",
        "lat": 34.5100, "lng": 36.5800,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Offensive starts, rebels still hold
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-06-05",
        "headline": "Government forces fully recapture Al-Qusayr from rebels",
        "location": "Qusayr",
        "lat": 34.5100, "lng": 36.5800,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-06-28",
        "headline": "Syrian Army captures town of Talkalakh near Lebanon border",
        "location": "Talkalakh",
        "lat": 34.6667, "lng": 36.2500,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-07-29",
        "headline": "Government troops retake Khalidiya district in Homs",
        "location": "Khalidiya",
        "lat": 34.7450, "lng": 36.7150,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-08-21",
        "headline": "Chemical attack reported in Ghouta suburbs of Damascus",
        "location": "Douma",
        "lat": 33.5714, "lng": 36.4014,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Rebels hold Ghouta
        "importance": 10,
        "category": "chemical"
    },
    {
        "date": "2013-10-25",
        "headline": "Kurdish YPG forces capture town of Yarubiyah on Iraq border",
        "location": "Yarubiyah",
        "lat": 36.8167, "lng": 42.0667,
        "controller_before": "Rebel Control",
        "controller_after": "SDF Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-11-15",
        "headline": "Government forces recapture Safira south of Aleppo",
        "location": "Safira",
        "lat": 36.0833, "lng": 37.3833,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-12-10",
        "headline": "Syrian Army captures Al-Nabk in Qalamoun region",
        "location": "Nabek",
        "lat": 34.0167, "lng": 36.7167,
        "controller_before": "Rebel Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "battle"
    },

    # --- ISIS EMERGES in late 2013 ---
    {
        "date": "2013-04-09",
        "headline": "ISIS announces expansion into Syria, claims Raqqa presence",
        "location": "Raqqa",
        "lat": 35.9524, "lng": 39.0120,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Not yet in control
        "importance": 9,
        "category": "political"
    },
    {
        "date": "2013-09-18",
        "headline": "ISIS seizes Azaz from rebels, first inter-rebel clash",
        "location": "Azaz",
        "lat": 36.5833, "lng": 37.0500,
        "controller_before": "Rebel Control",
        "controller_after": "Rebel Control",  # Rebels retake it shortly after
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2013-11-20",
        "headline": "ISIS fully takes control of Raqqa city, expels rebel groups",
        "location": "Raqqa",
        "lat": 35.9524, "lng": 39.0120,
        "controller_before": "Rebel Control",
        "controller_after": "ISIS Control",
        "importance": 10,
        "category": "battle"
    },
    {
        "date": "2013-11-25",
        "headline": "ISIS establishes checkpoint control along Raqqa-Deir ez-Zor highway",
        "location": "Tabqa",
        "lat": 35.8333, "lng": 38.5500,
        "controller_before": "Rebel Control",
        "controller_after": "ISIS Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2013-12-20",
        "headline": "ISIS takes control of areas in eastern Aleppo countryside",
        "location": "Jarablus",
        "lat": 36.8167, "lng": 38.0111,
        "controller_before": "Rebel Control",
        "controller_after": "ISIS Control",
        "importance": 5,
        "category": "battle"
    },

    # --- Kurdish YPG gains in the northeast ---
    {
        "date": "2012-07-19",
        "headline": "Kurdish PYD forces take control of Kobani/Ain al-Arab",
        "location": "Kobani",
        "lat": 36.8919, "lng": 38.3525,
        "controller_before": "Government Control",
        "controller_after": "SDF Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2012-07-20",
        "headline": "Kurdish forces seize Amuda in Hasakah province",
        "location": "Amuda",
        "lat": 37.0667, "lng": 40.9167,
        "controller_before": "Government Control",
        "controller_after": "SDF Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2012-07-21",
        "headline": "YPG takes control of Afrin in northwestern Syria",
        "location": "Afrin",
        "lat": 36.5167, "lng": 36.8667,
        "controller_before": "Government Control",
        "controller_after": "SDF Control",
        "importance": 6,
        "category": "battle"
    },
    {
        "date": "2012-11-10",
        "headline": "Kurds consolidate control over Qamishli suburbs",
        "location": "Qamishli",
        "lat": 37.0526, "lng": 41.2263,
        "controller_before": "Government Control",
        "controller_after": "SDF Control",
        "importance": 7,
        "category": "battle"
    },
    {
        "date": "2013-07-16",
        "headline": "YPG forces capture Ras al-Ain from rebels and jihadists",
        "location": "Ras al-Ain",
        "lat": 36.8500, "lng": 40.0667,
        "controller_before": "Rebel Control",
        "controller_after": "SDF Control",
        "importance": 5,
        "category": "battle"
    },
    {
        "date": "2013-08-01",
        "headline": "Kurdish forces take Malikiyah in far northeast",
        "location": "Malikiyah",
        "lat": 37.1667, "lng": 42.1333,
        "controller_before": "Government Control",
        "controller_after": "SDF Control",
        "importance": 5,
        "category": "battle"
    },

    # --- Government strongholds that never flipped ---
    {
        "date": "2011-03-01",
        "headline": "Damascus remains fully under government control",
        "location": "Damascus",
        "lat": 33.5138, "lng": 36.2765,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 10,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Homs city center under government control",
        "location": "Homs",
        "lat": 34.7324, "lng": 36.7137,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 9,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Hama under government control at start of conflict",
        "location": "Hama",
        "lat": 35.1318, "lng": 36.7578,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 8,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Deir ez-Zor under government control at start of conflict",
        "location": "Deir ez-Zor",
        "lat": 35.3359, "lng": 40.1408,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 8,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Hasakah under government control at start of conflict",
        "location": "Hasakah",
        "lat": 36.5024, "lng": 40.7429,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 7,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Sweida under government control at start of conflict",
        "location": "Sweida",
        "lat": 32.7089, "lng": 36.5695,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 6,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Quneitra under government control at start of conflict",
        "location": "Quneitra",
        "lat": 33.1250, "lng": 35.8250,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Salamiyah under government control at start of conflict",
        "location": "Salamiyah",
        "lat": 35.0167, "lng": 37.0500,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Palmyra under government control at start of conflict",
        "location": "Palmyra",
        "lat": 34.5600, "lng": 38.2672,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 6,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Bukamal under government control at start of conflict",
        "location": "Bukamal",
        "lat": 34.4500, "lng": 40.9167,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "political"
    },
    {
        "date": "2011-03-01",
        "headline": "Mayadin under government control at start of conflict",
        "location": "Mayadin",
        "lat": 35.0167, "lng": 40.4500,
        "controller_before": "Government Control",
        "controller_after": "Government Control",
        "importance": 5,
        "category": "political"
    },

    # --- Douma/Ghouta flips to rebel in mid-2012 ---
    {
        "date": "2012-10-20",
        "headline": "Rebels establish stronghold in Douma, Eastern Ghouta",
        "location": "Douma",
        "lat": 33.5714, "lng": 36.4014,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 7,
        "category": "battle"
    },

    # --- Daraa countryside rebel expansion ---
    {
        "date": "2013-02-10",
        "headline": "Rebels capture Sanamayn in northern Daraa",
        "location": "Sanamayn",
        "lat": 33.0667, "lng": 36.1833,
        "controller_before": "Government Control",
        "controller_after": "Rebel Control",
        "importance": 5,
        "category": "battle"
    },
]
