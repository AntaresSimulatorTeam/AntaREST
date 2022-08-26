import {
  ClusterElement,
  LinkClusterItem,
  LinkCreationInfoDTO,
} from "../../../../../../../common/types";
import { getBindingConstraint } from "../../../../../../../services/api/studydata";

type OperatorType = "less" | "equal" | "greater" | "both";
type FilteringType = "hourly" | "daily" | "weekly";

export interface ConstraintType {
  id: string;
  weight: number;
  offset?: number;
  data: LinkCreationInfoDTO | ClusterElement;
}

export interface BindingConstFields {
  name: string;
  id: string;
  enabled: boolean;
  time_step: FilteringType;
  operator: OperatorType;
  comments?: string;
  constraints: Array<ConstraintType>;
}

export type BindingConstPath = Record<keyof BindingConstFields, string>;

export async function getDefaultValues(
  studyId: string,
  bindingConstId: string
): Promise<BindingConstFields> {
  // Fetch fields
  const fields: BindingConstFields = await getBindingConstraint(
    studyId,
    bindingConstId
  );
  return { ...fields, comments: fields.comments || "" };
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
  if (index1 < 0) return false;

  const index2 = list[index1].item_list.findIndex((item) => item.id === value2);
  if (index2 < 0) return false;

  return true;
};

export const isTermExist = (
  list: Array<ConstraintType>,
  termId: string
): boolean => {
  return list.findIndex((item) => item.id === termId) >= 0;
};
