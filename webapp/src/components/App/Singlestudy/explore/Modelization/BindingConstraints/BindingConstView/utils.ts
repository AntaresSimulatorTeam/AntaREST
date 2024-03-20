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

/**
 * !WARNING: Temporary Workaround (Model adapter)
 * The following functions serves as a workaround to align the API's data model with the UI's requirements due to the current mismatch
 * between the expected data formats. Specifically, it toggles the input format between a string and an array of strings
 * (or in this context, OutputFilters) to accommodate the UI's handling of these fields.
 *
 * This transformation is necessary because the API currently provides these fields in a format not directly usable by the UI,
 * necessitating their conversion. It is important to note that this approach may introduce maintenance overhead and potential
 * points of failure, as it relies on the specific current structure of the API responses and UI expectations.
 *
 * Ideally, this transformation should be removed once the API's model is updated to natively support the data formats
 * required by the UI, thereby eliminating the need for such manual conversions and ensuring a more robust and direct
 * data flow between the API and the UI components.
 *
 * TODO: Monitor the API model updates and remove this workaround when possible, ensuring direct compatibility.
 */

/**
 * Checks if a given array consists only of valid OutputFilter values.
 *
 * @param array - The array to be checked.
 * @returns True if all items in the array are valid OutputFilter values, false otherwise.
 */
function isValidOutputFilterInput(array: string[]): array is OutputFilter[] {
  return array.every((item) => OUTPUT_FILTERS.includes(item as OutputFilter));
}

/**
 * Converts between a string and an array of OutputFilter values, depending on the input type.
 *
 * @param data - The data to be converted.
 * @returns The converted data.
 * @throws If the input is neither a string nor an array of OutputFilter values.
 */
function adaptOutputFilterFormat(
  data: string | OutputFilter[],
): string | OutputFilter[] {
  // Handle empty string as an empty array of filters.
  if (typeof data === "string") {
    if (data.length === 0) {
      return [];
    }

    // Convert filters string to array.
    const filtersArray = data.split(", ");

    if (isValidOutputFilterInput(filtersArray)) {
      return filtersArray;
    } else {
      throw new Error("String contains invalid output filters values");
    }
  }

  // Convert filters array to string, handling empty array as an empty string.
  if (Array.isArray(data)) {
    if (data.length === 0) {
      return "";
    }

    if (isValidOutputFilterInput(data)) {
      return data.join(", ");
    } else {
      throw new Error("Array contains invalid output filters values");
    }
  }

  throw new Error(
    "Invalid input: Expected a string or an array of OutputFilter values",
  );
}

/**
 * Adapts fields within a BindingConstraint object to match the expected data formats, facilitating
 * the alignment of API data with UI requirements.
 *
 * @param data - The BindingConstraint object to transform.
 * @returns The transformed BindingConstraint object.
 */
export function bindingConstraintModelAdapter(
  data: BindingConstraint,
): BindingConstraint {
  const filterSynthesis = adaptOutputFilterFormat(data.filter_synthesis);
  const filterYearByYear = adaptOutputFilterFormat(data.filter_year_by_year);

  return {
    ...data,
    filter_synthesis: filterSynthesis as typeof data.filter_synthesis,
    filter_year_by_year: filterYearByYear as typeof data.filter_year_by_year,
  };
}
