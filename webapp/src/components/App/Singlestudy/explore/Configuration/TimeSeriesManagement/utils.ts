import { DeepPartial } from "react-hook-form";
import { StudyMetadata } from "../../../../../../common/types";
import client from "../../../../../../services/api/client";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export enum TSType {
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

interface TSFormFieldsForType {
  stochasticTsStatus: boolean;
  number: number;
  refresh: boolean;
  refreshInterval: number;
  seasonCorrelation: SeasonCorrelation;
  storeInInput: boolean;
  storeInOutput: boolean;
  intraModal: boolean;
  interModal: boolean;
}

export interface TSFormFields
  extends Record<
    Exclude<TSType, TSType.Thermal | TSType.Renewables | TSType.NTC>,
    TSFormFieldsForType
  > {
  [TSType.Thermal]: Omit<TSFormFieldsForType, "seasonCorrelation">;
  [TSType.Renewables]: Pick<
    TSFormFieldsForType,
    "stochasticTsStatus" | "intraModal" | "interModal"
  >;
  [TSType.NTC]: Pick<TSFormFieldsForType, "stochasticTsStatus" | "intraModal">;
}

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SEASONAL_CORRELATION_OPTIONS = Object.values(SeasonCorrelation);

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

function makeRequestURL(studyId: StudyMetadata["id"]): string {
  return `v1/studies/${studyId}/config/timeseries_form_fields`;
}

export async function getTimeSeriesFormFields(
  studyId: StudyMetadata["id"]
): Promise<TSFormFields> {
  const res = await client.get(makeRequestURL(studyId));
  return res.data;
}

export function setTimeSeriesFormFields(
  studyId: StudyMetadata["id"],
  values: DeepPartial<TSFormFields>
): Promise<void> {
  return client.put(makeRequestURL(studyId), values);
}
