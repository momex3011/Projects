import {
  buildReportTargetId,
  CAMPUS_SURVEY_COOLDOWN_MINUTES,
  CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES,
  CAMPUS_SURVEY_LOCATIONS,
  CAMPUS_SURVEY_REWARD_POINTS,
  type CampusLocationType,
  type CrowdLevelId,
  formatCampusLocationLabel,
  getCampusLocationById,
  getCrowdOptionById,
  getNoiseOptionById,
  type NoiseLevelId,
} from "@/constants/campus-survey";
import {
  collection,
  doc,
  runTransaction,
  serverTimestamp,
  Timestamp,
} from "firebase/firestore";
import { db } from "./firebase";
import {
  buildContributionProgressFields,
  buildDefaultUserProfile,
  type UserProfileShape,
} from "./user-profile";

type FirestoreTimestampLike = Timestamp | Date | { toDate: () => Date } | null | undefined;

export type CampusReportDocument = {
  location: string;
  locationId: string;
  locationLabel: string;
  locationType: CampusLocationType;
  floor: number | null;
  reportTargetId: string;
  crowdLevel: CrowdLevelId;
  crowdLabel: string;
  noiseLevel: NoiseLevelId;
  noiseLabel: string;
  pointsAwarded: number;
  createdAt: Timestamp | null;
  userId: string;
};

export type SubmitCampusSurveyInput = {
  userId: string;
  locationId: string;
  floor?: number | null;
  crowdLevel: CrowdLevelId;
  noiseLevel: NoiseLevelId;
};

export type SubmitCampusSurveyResult =
  | {
      status: "success";
      locationLabel: string;
      pointsAwarded: number;
    }
  | {
      status: "duplicate";
      locationLabel: string;
      duplicateWindowMinutes: number;
    }
  | {
      status: "cooldown";
      minutesLeft: number;
    };

export type NormalizedCampusReport = {
  locationId: string;
  locationLabel: string;
  locationType: CampusLocationType;
  floor: number | null;
  reportTargetId: string;
  crowdLevel: CrowdLevelId;
  noiseLevel: NoiseLevelId;
  createdAt: Date | null;
};

export type AggregatedReportSummary = {
  crowdLevel: CrowdLevelId;
  crowdLabel: string;
  noiseLevel: NoiseLevelId;
  noiseLabel: string;
  reportCount: number;
  confidenceScore: number;
  confidenceLabel: "Low" | "Medium" | "High";
  updatedMinutesAgo: number | null;
};

export type AggregatedLocationSummary = {
  overall: AggregatedReportSummary;
  floors?: Partial<Record<number, AggregatedReportSummary>>;
};

export async function submitCampusSurveyReport({
  userId,
  locationId,
  floor,
  crowdLevel,
  noiseLevel,
}: SubmitCampusSurveyInput): Promise<SubmitCampusSurveyResult> {
  const location = getCampusLocationById(locationId);
  if (!location) {
    throw new Error("Please choose a valid campus location.");
  }

  const locationLabel = formatCampusLocationLabel(locationId, floor);
  const reportTargetId = buildReportTargetId(locationId, floor);
  const duplicateKey = `${userId}__${reportTargetId}__${crowdLevel}__${noiseLevel}`.toLowerCase();

  const userRef = doc(db, "users", userId);
  const duplicateRef = doc(db, "campusReportDedupes", duplicateKey);
  const reportRef = doc(collection(db, "campusReports"));

  return runTransaction(db, async (transaction) => {
    const userSnap = await transaction.get(userRef);
    const duplicateSnap = await transaction.get(duplicateRef);

    const userData = (userSnap.exists()
      ? (userSnap.data() as UserProfileShape)
      : buildDefaultUserProfile({ lastReportTime: null })) as UserProfileShape;

    const currentPoints = typeof userData.points === "number" ? userData.points : 0;
    const lastReportTime = toDate(userData.lastReportTime as FirestoreTimestampLike);
    const duplicateSubmittedAt = toDate(duplicateSnap.data()?.lastSubmittedAt);
    const now = new Date();
    const contributionProgress = buildContributionProgressFields(userData, now);

    if (
      duplicateSubmittedAt &&
      now.getTime() - duplicateSubmittedAt.getTime() <
        CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES * 60 * 1000
    ) {
      return {
        status: "duplicate",
        locationLabel,
        duplicateWindowMinutes: CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES,
      };
    }

    if (
      lastReportTime &&
      now.getTime() - lastReportTime.getTime() < CAMPUS_SURVEY_COOLDOWN_MINUTES * 60 * 1000
    ) {
      const minutesLeft = Math.ceil(
        (CAMPUS_SURVEY_COOLDOWN_MINUTES * 60 * 1000 -
          (now.getTime() - lastReportTime.getTime())) /
          60000
      );

      return {
        status: "cooldown",
        minutesLeft,
      };
    }

    const crowd = getCrowdOptionById(crowdLevel);
    const noise = getNoiseOptionById(noiseLevel);

    transaction.set(reportRef, {
      location: locationLabel,
      locationId,
      locationLabel,
      locationType: location.type,
      floor: location.floors?.length ? floor ?? null : null,
      reportTargetId,
      crowdLevel,
      crowdLabel: crowd.label,
      noiseLevel,
      noiseLabel: noise.label,
      pointsAwarded: CAMPUS_SURVEY_REWARD_POINTS,
      createdAt: serverTimestamp() as Timestamp,
      userId,
    });

    transaction.set(
      userRef,
      {
        ...(userSnap.exists() ? {} : buildDefaultUserProfile()),
        points: currentPoints + CAMPUS_SURVEY_REWARD_POINTS,
        lastReportTime: serverTimestamp(),
        ...contributionProgress,
      },
      { merge: true }
    );

    transaction.set(
      duplicateRef,
      {
        userId,
        reportTargetId,
        locationId,
        locationLabel,
        crowdLevel,
        noiseLevel,
        lastSubmittedAt: serverTimestamp(),
      },
      { merge: true }
    );

    return {
      status: "success",
      locationLabel,
      pointsAwarded: CAMPUS_SURVEY_REWARD_POINTS,
    };
  });
}

export function normalizeCampusReport(data: Record<string, unknown>): NormalizedCampusReport | null {
  const directLocationId = typeof data.locationId === "string" ? data.locationId : null;
  const directLocation = directLocationId ? getCampusLocationById(directLocationId) : null;
  const location = directLocation
    ? {
        locationId: directLocation.id,
        locationType: directLocation.type,
        floor: null,
      }
    : resolveLegacyLocation(data.location);

  if (!location) return null;

  const floor =
    typeof data.floor === "number" && Number.isFinite(data.floor)
      ? data.floor
      : location.floor;
  const createdAt = toDate(data.createdAt as FirestoreTimestampLike);
  const locationLabel =
    typeof data.locationLabel === "string"
      ? data.locationLabel
      : formatCampusLocationLabel(location.locationId, floor);
  const reportTargetId =
    typeof data.reportTargetId === "string"
      ? data.reportTargetId
      : buildReportTargetId(location.locationId, floor);

  return {
    locationId: location.locationId,
    locationLabel,
    locationType: location.locationType,
    floor,
    reportTargetId,
    crowdLevel: normalizeCrowdLevel(data.crowdLevel),
    noiseLevel: normalizeNoiseLevel(data.noiseLevel),
    createdAt,
  };
}

export function aggregateCampusReports(
  reports: NormalizedCampusReport[],
  now: Date = new Date()
): Record<string, AggregatedLocationSummary> {
  const buckets: Record<string, NormalizedCampusReport[]> = {};
  const floorBuckets: Record<string, Record<number, NormalizedCampusReport[]>> = {};

  for (const report of reports) {
    if (!buckets[report.locationId]) buckets[report.locationId] = [];
    buckets[report.locationId].push(report);

    if (typeof report.floor === "number") {
      if (!floorBuckets[report.locationId]) floorBuckets[report.locationId] = {};
      if (!floorBuckets[report.locationId][report.floor]) {
        floorBuckets[report.locationId][report.floor] = [];
      }
      floorBuckets[report.locationId][report.floor].push(report);
    }
  }

  const result: Record<string, AggregatedLocationSummary> = {};

  for (const [locationId, locationReports] of Object.entries(buckets)) {
    const overall = aggregateReportBucket(locationReports, now);
    if (!overall) continue;

    const locationFloors = floorBuckets[locationId];
    const floors = locationFloors
      ? Object.fromEntries(
          Object.entries(locationFloors)
            .map(([floorValue, floorReports]) => [
              Number(floorValue),
              aggregateReportBucket(floorReports, now),
            ])
            .filter((entry): entry is [number, AggregatedReportSummary] => entry[1] !== null)
        )
      : undefined;

    result[locationId] = {
      overall,
      ...(floors && Object.keys(floors).length > 0 ? { floors } : {}),
    };
  }

  return result;
}

export function normalizeCrowdLevel(raw: unknown): CrowdLevelId {
  if (typeof raw !== "string") return "low";
  const value = raw.toLowerCase().trim();

  if (
    value.includes("high") ||
    value.includes("packed") ||
    value.includes("busy") ||
    value.includes("crowded")
  ) {
    return "high";
  }

  if (
    value.includes("medium") ||
    value.includes("moderate") ||
    value.includes("steady") ||
    value.includes("mid")
  ) {
    return "medium";
  }

  return "low";
}

export function normalizeNoiseLevel(raw: unknown): NoiseLevelId {
  if (typeof raw !== "string") return "quiet";
  const value = raw.toLowerCase().trim();

  if (
    value.includes("loud") ||
    value.includes("social") ||
    value.includes("noisy") ||
    value.includes("busy")
  ) {
    return "loud";
  }

  if (
    value.includes("moderate") ||
    value.includes("normal") ||
    value.includes("chatter") ||
    value.includes("buzz")
  ) {
    return "moderate";
  }

  return "quiet";
}

function aggregateReportBucket(
  reports: NormalizedCampusReport[],
  now: Date
): AggregatedReportSummary | null {
  if (reports.length === 0) return null;

  let weightedCrowd = 0;
  let weightedNoise = 0;
  let totalWeight = 0;
  let newestReport: Date | null = null;

  for (const report of reports) {
    const weight = getRecencyWeight(report.createdAt, now);
    weightedCrowd += getCrowdOptionById(report.crowdLevel).score * weight;
    weightedNoise += getNoiseOptionById(report.noiseLevel).score * weight;
    totalWeight += weight;

    if (!newestReport || (report.createdAt && report.createdAt > newestReport)) {
      newestReport = report.createdAt;
    }
  }

  const crowdLevel = scoreToCrowdLevel(weightedCrowd / Math.max(totalWeight, 1));
  const noiseLevel = scoreToNoiseLevel(weightedNoise / Math.max(totalWeight, 1));
  const confidenceScore = calculateConfidenceScore(reports.length, newestReport, now);

  return {
    crowdLevel,
    crowdLabel: getCrowdOptionById(crowdLevel).label,
    noiseLevel,
    noiseLabel: getNoiseOptionById(noiseLevel).label,
    reportCount: reports.length,
    confidenceScore,
    confidenceLabel: getConfidenceLabel(confidenceScore),
    updatedMinutesAgo: newestReport
      ? Math.max(0, Math.round((now.getTime() - newestReport.getTime()) / 60000))
      : null,
  };
}

function calculateConfidenceScore(reportCount: number, newestReport: Date | null, now: Date) {
  const volumeScore = Math.min(reportCount / 5, 1);

  let freshnessScore = 0.3;
  if (newestReport) {
    const ageMinutes = (now.getTime() - newestReport.getTime()) / 60000;
    if (ageMinutes <= 30) freshnessScore = 1;
    else if (ageMinutes <= 90) freshnessScore = 0.8;
    else if (ageMinutes <= 180) freshnessScore = 0.6;
  }

  return Math.round((volumeScore * 0.7 + freshnessScore * 0.3) * 100);
}

function getConfidenceLabel(score: number): "Low" | "Medium" | "High" {
  if (score >= 75) return "High";
  if (score >= 45) return "Medium";
  return "Low";
}

function getRecencyWeight(createdAt: Date | null, now: Date) {
  if (!createdAt) return 0.45;

  const ageMinutes = (now.getTime() - createdAt.getTime()) / 60000;
  if (ageMinutes <= 30) return 1.25;
  if (ageMinutes <= 90) return 1;
  if (ageMinutes <= 180) return 0.7;
  return 0.45;
}

function scoreToCrowdLevel(score: number): CrowdLevelId {
  if (score >= 2.5) return "high";
  if (score >= 1.75) return "medium";
  return "low";
}

function scoreToNoiseLevel(score: number): NoiseLevelId {
  if (score >= 2.5) return "loud";
  if (score >= 1.75) return "moderate";
  return "quiet";
}

function resolveLegacyLocation(raw: unknown):
  | {
      locationId: string;
      locationType: CampusLocationType;
      floor: number | null;
    }
  | null {
  if (typeof raw !== "string") return null;

  const normalized = raw.toLowerCase().trim();
  const floor = extractFloor(raw);

  const location =
    CAMPUS_SURVEY_LOCATIONS.find((entry) => normalized.includes(entry.label.toLowerCase())) ??
    CAMPUS_SURVEY_LOCATIONS.find(
      (entry) => entry.mapTitle && normalized.includes(entry.mapTitle.toLowerCase())
    );

  if (!location) return null;

  return {
    locationId: location.id,
    locationType: location.type,
    floor,
  };
}

function extractFloor(raw: string) {
  const match = raw.match(/floor\s+(\d+)/i);
  if (!match) return null;

  const floor = Number(match[1]);
  return Number.isFinite(floor) ? floor : null;
}

function toDate(value: FirestoreTimestampLike) {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (value instanceof Timestamp) return value.toDate();
  if (typeof value?.toDate === "function") return value.toDate();
  return null;
}
