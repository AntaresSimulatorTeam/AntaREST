import { StudyMetadata } from "../../../../../../common/types";
import client from "../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

enum Mode {
  Economy = "Economy",
  Adequacy = "Adequacy",
  Draft = "draft",
}

enum BuildingMode {
  Automatic = "Automatic",
  Custom = "Custom",
  Derated = "Derated",
}

enum Month {
  January = "january",
  February = "february",
  March = "march",
  April = "april",
  May = "may",
  June = "june",
  July = "july",
  August = "august",
  September = "september",
  October = "october",
  November = "november",
  December = "december",
}

enum WeekDay {
  Monday = "Monday",
  Tuesday = "Tuesday",
  Wednesday = "Wednesday",
  Thursday = "Thursday",
  Friday = "Friday",
  Saturday = "Saturday",
  Sunday = "Sunday",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface GeneralFormFields {
  mode: Mode;
  firstDay: number;
  lastDay: number;
  horizon: string;
  firstMonth: Month;
  firstWeekDay: WeekDay;
  firstJanuary: WeekDay;
  leapYear: boolean;
  nbYears: number;
  buildingMode: BuildingMode;
  selectionMode: boolean;
  yearByYear: boolean;
  simulationSynthesis: boolean;
  mcScenario: boolean;
  // Geographic trimming + Thematic trimming.
  // For study versions < 710
  filtering?: boolean;
  // For study versions >= 710
  geographicTrimming?: boolean;
  thematicTrimming?: boolean;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

// TODO i18n

export const YEAR_OPTIONS: Array<{ label: string; value: Month }> = [
  { label: "JAN - DEC", value: Month.January },
  { label: "FEB - JAN", value: Month.February },
  { label: "MAR - FEB", value: Month.March },
  { label: "APR - MAR", value: Month.April },
  { label: "MAY - APR", value: Month.May },
  { label: "JUN - MAY", value: Month.June },
  { label: "JUL - JUN", value: Month.July },
  { label: "AUG - JUL", value: Month.August },
  { label: "SEP - AUG", value: Month.September },
  { label: "OCT - SEP", value: Month.October },
  { label: "NOV - OCT", value: Month.November },
  { label: "DEC - NOV", value: Month.December },
];

export const WEEK_OPTIONS: Array<{ label: string; value: WeekDay }> = [
  { label: "MON - SUN", value: WeekDay.Monday },
  { label: "TUE - MON", value: WeekDay.Tuesday },
  { label: "WED - TUE", value: WeekDay.Wednesday },
  { label: "THU - WED", value: WeekDay.Thursday },
  { label: "FRI - THU", value: WeekDay.Friday },
  { label: "SAT - FRI", value: WeekDay.Saturday },
  { label: "SUN - SAT", value: WeekDay.Sunday },
];

export const FIRST_JANUARY_OPTIONS = Object.values(WeekDay);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/general_form_fields`;
}

export async function getGeneralFormFields(
  studyId: StudyMetadata["id"]
): Promise<GeneralFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setGeneralFormFields(
  studyId: StudyMetadata["id"],
  values: Partial<GeneralFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
