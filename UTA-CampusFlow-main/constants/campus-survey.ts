import { UTA } from "./theme";

export type CampusLocationType = "academic" | "student" | "dining";
export type CrowdLevelId = "low" | "medium" | "high";
export type NoiseLevelId = "quiet" | "moderate" | "loud";

export type SurveyChoiceOption<T extends string> = {
  id: T;
  label: string;
  shortLabel: string;
  description: string;
  color: string;
  score: number;
};

export type CampusSurveyLocation = {
  id: string;
  label: string;
  short: string;
  row: number;
  col: number;
  type: CampusLocationType;
  floors?: number[];
  mapTitle?: string;
  coordinate: {
    latitude: number;
    longitude: number;
  };
};

export const CAMPUS_SURVEY_REWARD_POINTS = 10;
export const CAMPUS_SURVEY_COOLDOWN_MINUTES = 30;
export const CAMPUS_SURVEY_DUPLICATE_WINDOW_MINUTES = 60;
export const CAMPUS_SURVEY_REPORT_WINDOW_HOURS = 3;

export const CROWD_LEVEL_OPTIONS: SurveyChoiceOption<CrowdLevelId>[] = [
  {
    id: "low",
    label: "Plenty of space",
    shortLabel: "Open",
    description: "Easy to find a seat or study spot.",
    color: UTA.green,
    score: 1,
  },
  {
    id: "medium",
    label: "Getting busy",
    shortLabel: "Busy",
    description: "Some activity around you, but still manageable.",
    color: UTA.yellow,
    score: 2,
  },
  {
    id: "high",
    label: "Packed",
    shortLabel: "Packed",
    description: "Expect lines, full tables, or limited room.",
    color: UTA.red,
    score: 3,
  },
];

export const NOISE_LEVEL_OPTIONS: SurveyChoiceOption<NoiseLevelId>[] = [
  {
    id: "quiet",
    label: "Quiet study",
    shortLabel: "Quiet",
    description: "Mostly silent or whisper-level noise.",
    color: "#4F8EF7",
    score: 1,
  },
  {
    id: "moderate",
    label: "Normal chatter",
    shortLabel: "Chatter",
    description: "Light talking and everyday campus buzz.",
    color: UTA.gold,
    score: 2,
  },
  {
    id: "loud",
    label: "Pretty loud",
    shortLabel: "Loud",
    description: "Conversations, groups, or activity stand out.",
    color: UTA.orange,
    score: 3,
  },
];

export const CAMPUS_SURVEY_LOCATIONS: CampusSurveyLocation[] = [
  {
    id: "nedderman-hall",
    label: "Nedderman Hall",
    short: "NH",
    row: 0,
    col: 0,
    type: "academic",
    coordinate: { latitude: 32.73232414728388, longitude: -97.11427682887216 },
  },
  {
    id: "ero-building",
    label: "ERB Building",
    short: "ERB",
    row: 0,
    col: 1,
    type: "academic",
    mapTitle: "Engineering Research Building",
    coordinate: { latitude: 32.733409747443545, longitude: -97.11272154250182 },
  },
  {
    id: "woolf-hall",
    label: "Woolf Hall",
    short: "WH",
    row: 0,
    col: 2,
    type: "academic",
    coordinate: { latitude: 32.73152634617023, longitude: -97.11264915556725 },
  },
  {
    id: "science-hall",
    label: "Science Hall",
    short: "SH",
    row: 1,
    col: 0,
    type: "academic",
    coordinate: { latitude: 32.73054354218558, longitude: -97.11363918495864 },
  },
  {
    id: "life-science",
    label: "Life Science",
    short: "LS",
    row: 1,
    col: 1,
    type: "academic",
    coordinate: { latitude: 32.728686396014524, longitude: -97.11231535250118 },
  },
  {
    id: "pickard-hall",
    label: "Pickard Hall",
    short: "PKH",
    row: 1,
    col: 2,
    type: "academic",
    coordinate: { latitude: 32.72903421499007, longitude: -97.1114049806393 },
  },
  {
    id: "college-of-business",
    label: "College of Business",
    short: "COBA",
    row: 2,
    col: 0,
    type: "academic",
    coordinate: { latitude: 32.72972273211371, longitude: -97.11059318810737 },
  },
  {
    id: "university-hall",
    label: "University Hall",
    short: "UH",
    row: 2,
    col: 1,
    type: "academic",
    coordinate: { latitude: 32.72909961387194, longitude: -97.11390421051703 },
  },
  {
    id: "trimble-hall",
    label: "Trimble Hall",
    short: "TH",
    row: 2,
    col: 2,
    type: "academic",
    coordinate: { latitude: 32.72968848602892, longitude: -97.11171409756815 },
  },
  {
    id: "university-center",
    label: "University Center",
    short: "UC",
    row: 3,
    col: 0,
    type: "student",
    mapTitle: "E.H. Hereford University Center",
    coordinate: { latitude: 32.73168448874286, longitude: -97.11099911672139 },
  },
  {
    id: "central-library",
    label: "Central Library",
    short: "LIB",
    row: 3,
    col: 1,
    type: "student",
    floors: [1, 2, 3, 4, 5, 6],
    coordinate: { latitude: 32.729718404681165, longitude: -97.1128425497474 },
  },
  {
    id: "mac-fitness",
    label: "MAC Fitness",
    short: "MAC",
    row: 3,
    col: 2,
    type: "student",
    coordinate: { latitude: 32.73200836183603, longitude: -97.11695477306283 },
  },
  {
    id: "commons",
    label: "The Commons",
    short: "COM",
    row: 4,
    col: 0,
    type: "dining",
    coordinate: { latitude: 32.73280887562872, longitude: -97.11708298458836 },
  },
  {
    id: "college-park-center",
    label: "College Park Center",
    short: "CPC",
    row: 4,
    col: 1,
    type: "student",
    coordinate: { latitude: 32.730672415834, longitude: -97.10804151314355 },
  },
  {
    id: "smart-hospital",
    label: "SMART Hospital",
    short: "SMRT",
    row: 4,
    col: 2,
    type: "academic",
    coordinate: { latitude: 32.7273272403283, longitude: -97.1113246809804 },
  },
];

export const LOCATION_TYPE_LABELS: Record<CampusLocationType, string> = {
  academic: "Academic Buildings",
  student: "Student Life",
  dining: "Dining & Services",
};

export const LOCATION_TYPE_HELPERS: Record<CampusLocationType, string> = {
  academic: "Classrooms, labs, and lecture spaces.",
  student: "Popular spots for studying, events, or hanging out.",
  dining: "Dining halls and food-heavy campus spaces.",
};

export const CAMPUS_SURVEY_LOCATION_SECTIONS = (["academic", "student", "dining"] as const).map(
  (type) => ({
    title: LOCATION_TYPE_LABELS[type],
    description: LOCATION_TYPE_HELPERS[type],
    data: CAMPUS_SURVEY_LOCATIONS.filter((location) => location.type === type),
  })
);

export function getCampusLocationById(locationId: string | null | undefined) {
  if (!locationId) return null;
  return CAMPUS_SURVEY_LOCATIONS.find((location) => location.id === locationId) ?? null;
}

export function formatCampusLocationLabel(locationId: string, floor?: number | null) {
  const location = getCampusLocationById(locationId);
  if (!location) return "";
  if (location.floors?.length && floor) {
    return `${location.label} Floor ${floor}`;
  }
  return location.label;
}

export function buildReportTargetId(locationId: string, floor?: number | null) {
  const location = getCampusLocationById(locationId);
  if (location?.floors?.length && floor) {
    return `${locationId}-floor-${floor}`;
  }
  return locationId;
}

export function getCrowdOptionById(level: CrowdLevelId) {
  return CROWD_LEVEL_OPTIONS.find((option) => option.id === level) ?? CROWD_LEVEL_OPTIONS[0];
}

export function getNoiseOptionById(level: NoiseLevelId) {
  return NOISE_LEVEL_OPTIONS.find((option) => option.id === level) ?? NOISE_LEVEL_OPTIONS[0];
}
