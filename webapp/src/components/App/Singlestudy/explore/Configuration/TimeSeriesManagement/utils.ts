import { StudyMetadata } from "../../../../../../common/types";
import { getStudyData } from "../../../../../../services/api/study";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum TimeSeriesType {
  Load = "load",
  Hydro = "hydro",
  Thermal = "thermal",
  Wind = "wind",
  Solar = "solar",
  Renewables = "renewables",
  NTC = "ntc",
}

enum SeasonCorrelation {
  Monthly = "monthly",
  Annual = "annual",
}

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface SettingsGeneralDataGeneral {
  generate: string;
  nbtimeseriesload: number;
  nbtimeserieshydro: number;
  nbtimeserieswind: number;
  nbtimeseriesthermal: number;
  nbtimeseriessolar: number;
  refreshtimeseries: string;
  refreshintervalload: number;
  refreshintervalhydro: number;
  refreshintervalwind: number;
  refreshintervalthermal: number;
  refreshintervalsolar: number;
  "intra-modal": string;
  "inter-modal": string;
}

type SettingsGeneralDataInput = {
  [key in Exclude<
    TimeSeriesType,
    TimeSeriesType.Thermal | TimeSeriesType.Renewables | TimeSeriesType.NTC
  >]: {
    prepro?: {
      correlation?: {
        general?: {
          mode?: SeasonCorrelation;
        };
      };
    };
  };
} & { import: string };

interface SettingsGeneralDataOutput {
  archives: string;
}

interface SettingsGeneralData {
  // For unknown reason, `general`, `input` and `output` may be empty
  general?: Partial<SettingsGeneralDataGeneral>;
  input?: Partial<SettingsGeneralDataInput>;
  output?: Partial<SettingsGeneralDataOutput>;
}

interface TimeSeriesValues {
  readyMadeTsStatus: boolean;
  stochasticTsStatus: boolean;
  number: number;
  refresh: boolean;
  refreshInterval: number;
  seasonCorrelation: SeasonCorrelation | undefined;
  storeInInput: boolean;
  storeInOutput: boolean;
  intraModal: boolean;
  interModal: boolean;
}

export type FormValues = Record<TimeSeriesType, TimeSeriesValues>;

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SEASONAL_CORRELATION_OPTIONS = Object.values(SeasonCorrelation);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeTimeSeriesValues(
  type: TimeSeriesType,
  data: SettingsGeneralData
): TimeSeriesValues {
  const { general = {}, output = {}, input = {} } = data;
  const {
    generate = "",
    refreshtimeseries = "",
    "intra-modal": intraModal = "",
    "inter-modal": interModal = "",
  } = general;
  const { import: imp = "" } = input;
  const { archives = "" } = output;
  const isGenerateHasType = generate.includes(type);
  const isSpecialType =
    type === TimeSeriesType.Renewables || type === TimeSeriesType.NTC;

  return {
    readyMadeTsStatus: !isGenerateHasType,
    stochasticTsStatus: isGenerateHasType,
    number: isSpecialType ? NaN : general[`nbtimeseries${type}`] ?? 1,
    refresh: refreshtimeseries.includes(type),
    refreshInterval: isSpecialType
      ? NaN
      : general[`refreshinterval${type}`] ?? 100,
    seasonCorrelation:
      isSpecialType || type === TimeSeriesType.Thermal
        ? undefined
        : input[type]?.prepro?.correlation?.general?.mode ||
          SeasonCorrelation.Annual,
    storeInInput: imp.includes(type),
    storeInOutput: archives.includes(type),
    intraModal: intraModal.includes(type),
    interModal: interModal.includes(type),
  };
}

export async function getFormValues(
  studyId: StudyMetadata["id"]
): Promise<FormValues> {
  const data = await getStudyData<SettingsGeneralData>(
    studyId,
    "settings/generaldata",
    2
  );

  return {
    load: makeTimeSeriesValues(TimeSeriesType.Load, data),
    thermal: makeTimeSeriesValues(TimeSeriesType.Thermal, data),
    hydro: makeTimeSeriesValues(TimeSeriesType.Hydro, data),
    wind: makeTimeSeriesValues(TimeSeriesType.Wind, data),
    solar: makeTimeSeriesValues(TimeSeriesType.Solar, data),
    renewables: makeTimeSeriesValues(TimeSeriesType.Renewables, data),
    ntc: makeTimeSeriesValues(TimeSeriesType.NTC, data),
  };
}
