import {
  ClusterElement,
  LinkClusterItem,
  LinkCreationInfoDTO,
} from "../../../../../../../common/types";
import { getBindingConstraint } from "../../../../../../../services/api/studydata";
import { FilteringType } from "../../../common/types";

type OperatorType = "less" | "equal" | "greater" | "both";

export interface ConstraintType {
  id: string;
  weight: number;
  offset?: number;
  data: LinkCreationInfoDTO | ClusterElement;
}

export interface UpdateBindingConstraint {
  key: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
}

export interface BindingConstFields {
  name: string;
  id: string;
  enabled: boolean;
  time_step: Exclude<FilteringType, "monthly" | "annual">;
  operator: OperatorType;
  comments?: string;
  filterByYear: Array<FilteringType>;
  filterSynthesis: Array<FilteringType>;
  constraints: Array<ConstraintType>;
}

export interface BindingConstFieldsDTO {
  name: string;
  id: string;
  enabled: boolean;
  time_step: Exclude<FilteringType, "monthly" | "annual">;
  operator: OperatorType;
  comments?: string;
  filter_year_by_year?: string;
  filter_synthesis?: string;
  constraints: Array<ConstraintType>;
}

export type BindingConstPath = Record<keyof BindingConstFields, string>;

export async function getDefaultValues(
  studyId: string,
  bindingConstId: string
): Promise<BindingConstFields> {
  // Fetch fields
  const fields: BindingConstFieldsDTO = await getBindingConstraint(
    studyId,
    bindingConstId
  );
  return {
    ...fields,
    comments: fields.comments || "",
    filterByYear: (fields.filter_year_by_year || "").split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
    filterSynthesis: (fields.filter_synthesis || "").split(",").map((elm) => {
      const sElm = elm.replace(/\s+/g, "");
      return sElm as FilteringType;
    }),
  };
}

export function isDataLink(
  data: LinkCreationInfoDTO | ClusterElement
): data is LinkCreationInfoDTO {
  return (data as LinkCreationInfoDTO).area1 !== undefined;
}

export function dataToId(data: LinkCreationInfoDTO | ClusterElement): string {
  if (isDataLink(data)) {
    const link = data;
    return `${link.area1}%${link.area2}`;
  }
  const cluster = data;
  return `${cluster.area}.${cluster.cluster}`;
}

export const isOptionExist = (
  list: Array<LinkClusterItem>,
  value1: string,
  value2: string
): boolean => {
  const index1 = list.findIndex((item) => item.element.id === value1);
  if (index1 < 0) {
    return false;
  }

  const index2 = list[index1].item_list.findIndex((item) => item.id === value2);
  if (index2 < 0) {
    return false;
  }

  return true;
};

export const isTermExist = (
  list: Array<ConstraintType>,
  termId: string
): boolean => {
  return list.findIndex((item) => item.id === termId) >= 0;
};

export const ACTIVE_WINDOWS_DOC_PATH =
  "https://antares-simulator.readthedocs.io/en/latest/reference-guide/04-active_windows/";
