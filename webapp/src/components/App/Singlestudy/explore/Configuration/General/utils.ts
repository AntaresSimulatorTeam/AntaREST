import * as RA from "ramda-adjunct";
import { StudyMetadata } from "../../../../../../common/types";
import {
  getStudyData,
  getThematicTrimmingConfig,
} from "../../../../../../services/api/study";
import {
  ThematicTrimmingConfig,
  formatThematicTrimmingConfigDTO,
} from "./dialogs/ThematicTrimmingDialog/utils";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

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

interface SettingsGeneralDataGeneral {
  // Mode
  mode: "Economy" | "Adequacy" | "draft";
  // First day
  "simulation.start": number;
  // Last day
  "simulation.end": number;
  // Horizon
  horizon: string;
  // Year
  "first-month-in-year": Month;
  // Week
  "first.weekday": WeekDay;
  // 1st January
  "january.1st": WeekDay;
  // Leap year
  leapyear: boolean;
  // Number
  nbyears: number;
  // Building mode
  "custom-ts-numbers": boolean;
  "custom-scenario": boolean; // For study versions >= 8
  derated: boolean;
  // Selection mode
  "user-playlist": boolean;
  // Year-by-year
  "year-by-year": boolean;
  // Geographic trimming
  "geographic-trimming": boolean;
  // Thematic trimming
  "thematic-trimming": boolean;
  // Geographic trimming + Thematic trimming
  filtering: boolean; // For study versions >= 710
}

interface SettingsGeneralDataOutput {
  // Simulation synthesis
  synthesis: boolean;
  // MC Scenario
  storenewset: boolean;
}

interface SettingsGeneralData {
  // For unknown reason, `general` and `output` may be empty
  general?: Partial<SettingsGeneralDataGeneral>;
  output?: Partial<SettingsGeneralDataOutput>;
}

export interface FormValues {
  mode: SettingsGeneralDataGeneral["mode"];
  firstDay: SettingsGeneralDataGeneral["simulation.start"];
  lastDay: SettingsGeneralDataGeneral["simulation.end"];
  horizon: SettingsGeneralDataGeneral["horizon"];
  firstMonth: SettingsGeneralDataGeneral["first-month-in-year"];
  firstWeekDay: SettingsGeneralDataGeneral["first.weekday"];
  firstJanuary: SettingsGeneralDataGeneral["january.1st"];
  leapYear: SettingsGeneralDataGeneral["leapyear"];
  nbYears: SettingsGeneralDataGeneral["nbyears"];
  buildingMode: "Automatic" | "Custom" | "Derated";
  selectionMode: SettingsGeneralDataGeneral["user-playlist"];
  simulationSynthesis: SettingsGeneralDataOutput["synthesis"];
  yearByYear: SettingsGeneralDataGeneral["year-by-year"];
  mcScenario: SettingsGeneralDataOutput["storenewset"];
  geographicTrimming: SettingsGeneralDataGeneral["geographic-trimming"];
  thematicTrimming: SettingsGeneralDataGeneral["thematic-trimming"];
  thematicTrimmingConfig: ThematicTrimmingConfig;
  filtering: SettingsGeneralDataGeneral["filtering"];
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

const DEFAULT_VALUES: Omit<FormValues, "thematicTrimmingConfig"> = {
  mode: "Economy",
  firstDay: 1,
  lastDay: 365,
  horizon: "",
  firstMonth: Month.January,
  firstWeekDay: WeekDay.Monday,
  firstJanuary: WeekDay.Monday,
  leapYear: false,
  nbYears: 1,
  buildingMode: "Automatic",
  selectionMode: false,
  simulationSynthesis: true,
  yearByYear: false,
  mcScenario: false,
  geographicTrimming: false,
  thematicTrimming: false,
  filtering: false,
};

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export async function getFormValues(
  studyId: StudyMetadata["id"]
): Promise<FormValues> {
  const { general = {}, output = {} } = await getStudyData<SettingsGeneralData>(
    studyId,
    "settings/generaldata",
    2
  );

  const {
    "custom-ts-numbers": customTsNumbers,
    "custom-scenario": customScenarios,
    derated,
    ...generalRest
  } = general;

  let buildingMode: FormValues["buildingMode"] = "Automatic";
  if (derated) {
    buildingMode = "Derated";
  }
  // 'custom-scenario' replaces 'custom-ts-numbers' in study versions >= 8
  else if (customScenarios || customTsNumbers) {
    buildingMode = "Custom";
  }

  const thematicTrimmingConfigDto = await getThematicTrimmingConfig(studyId);

  return {
    ...DEFAULT_VALUES,
    ...RA.renameKeys(
      {
        "simulation.start": "firstDay",
        "simulation.end": "lastDay",
        "first-month-in-year": "firstMonth",
        "first.weekday": "firstWeekDay",
        "january.1st": "firstJanuary",
        leapyear: "leapYear",
        nbyears: "nbYears",
        "user-playlist": "selectionMode",
        "year-by-year": "yearByYear",
        "geographic-trimming": "geographicTrimming",
        "thematic-trimming": "thematicTrimming",
      },
      generalRest
    ),
    ...RA.renameKeys(
      {
        synthesis: "simulationSynthesis",
        storenewset: "mcScenario",
      },
      output
    ),
    buildingMode,
    thematicTrimmingConfig: formatThematicTrimmingConfigDTO(
      thematicTrimmingConfigDto
    ),
  };
}
