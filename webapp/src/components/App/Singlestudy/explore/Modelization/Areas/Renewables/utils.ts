import * as R from "ramda";
import { FieldValues } from "react-hook-form";
import { Cluster, StudyMetadata } from "../../../../../../../common/types";
import {
  editStudy,
  getStudyData,
} from "../../../../../../../services/api/study";

type TsModeType = "power generation" | "production factor";

export interface RenewableType {
  name: string;
  group?: string;
  "ts-interpretation": TsModeType;
  enabled: boolean; // Default: true
  unitcount: number; // Default: 0
  nominalcapacity: number; // Default: 0
}

export interface RenewableFields extends FieldValues {
  name: string;
  group?: string;
  tsInterpretation: TsModeType;
  enabled?: boolean; // Default: true
  unitcount?: number; // Default: 0
  nominalCapacity?: number; // Default: 0
}

export type RenewablePath = Record<keyof RenewableFields, string>;

export async function getDefaultValues(
  studyId: string,
  area: string,
  cluster: Cluster["id"]
): Promise<RenewableFields> {
  const pathPrefix = `input/renewables/clusters/${area}/list/${cluster}`;
  const data: RenewableType = await getStudyData(studyId, pathPrefix, 3);
  return {
    name: data.name,
    group: data.group,
    enabled: data.enabled !== undefined ? data.enabled : true,
    unitcount: data.unitcount || 0,
    nominalCapacity: data.nominalcapacity || 0,
    tsInterpretation: data["ts-interpretation"] || "power generation",
  };
}

export function getRenewablePath(area: string, cluster: string): RenewablePath {
  const pathPrefix = `input/renewables/clusters/${area}/list/${cluster}`;
  return {
    name: `${pathPrefix}/name`,
    group: `${pathPrefix}/group`,
    enabled: `${pathPrefix}/enabled`,
    unitcount: `${pathPrefix}/unitcount`,
    nominalCapacity: `${pathPrefix}/nominalcapacity`,
    tsInterpretation: `${pathPrefix}/ts-interpretation`,
  };
}

export const saveField = R.curry(
  (
    studyId: StudyMetadata["id"],
    pathPrefix: string,
    path: { [elm: string]: string },
    defaultValues: any,
    noDataValue: any,
    name: string,
    data: any
  ): Promise<void> => {
    if (data === noDataValue || data === undefined) {
      const { [name]: ignore, ...toEdit } = defaultValues;
      return editStudy(toEdit, studyId, pathPrefix);
    }
    return editStudy(data, studyId, path[name]);
  }
);

export const tsModeOptions = ["power generation", "production factor"].map(
  (item) => ({
    label: item,
    value: item,
  })
);

export const fixedGroupList = [
  "Wind Onshore",
  "Wind Offshore",
  "Solar Thermal",
  "Solar PV",
  "Solar Rooftop",
  "Other RES 1",
  "Other RES 2",
  "Other RES 3",
  "Other RES 4",
];
