import {
  ClusterElement,
  LinkClusterItem,
  LinkCreationInfoDTO,
} from "../../../../../../../common/types";

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const ACTIVE_WINDOWS_DOC_PATH =
  "https://antares-simulator.readthedocs.io/en/latest/reference-guide/04-active_windows/";

export const BC_PATH = `input/bindingconstraints/bindingconstraints`;
export const OPERATORS = ["less", "equal", "greater", "both"] as const;
export const TIME_STEPS = ["hourly", "daily", "weekly"] as const;
export const OUTPUT_FILTERS = [
  "hourly",
  "daily",
  "weekly",
  "monthly",
  "annual",
] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type Operator = (typeof OPERATORS)[number];
export type TimeStep = (typeof TIME_STEPS)[number];
export type OutputFilter = (typeof OUTPUT_FILTERS)[number];

export interface ConstraintTerm {
  id: string;
  weight: number;
  offset?: number;
  data: LinkCreationInfoDTO | ClusterElement; // TODO remove, and create better types
}

export interface BindingConstraint {
  id: string;
  name: string;
  group: string;
  enabled: boolean;
  time_step: TimeStep;
  operator: Operator;
  comments?: string;
  filter_synthesis: OutputFilter[];
  filter_year_by_year: OutputFilter[];
  constraints: ConstraintTerm[];
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

//TODO optimize utils
export function isDataLink(
  data: LinkCreationInfoDTO | ClusterElement,
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
  list: LinkClusterItem[],
  value1: string,
  value2: string,
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
  terms: ConstraintTerm[],
  termId: string,
): boolean => {
  return terms.findIndex((term) => term.id === termId) >= 0;
};
