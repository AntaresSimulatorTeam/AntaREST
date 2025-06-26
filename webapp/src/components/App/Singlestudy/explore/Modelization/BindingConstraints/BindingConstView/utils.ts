/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const ACTIVE_WINDOWS_DOC_PATH =
  "https://antares-simulator.readthedocs.io/en/latest/reference-guide/04-active_windows/";

export const OPERATORS = ["less", "equal", "greater", "both"] as const;
export const TIME_STEPS = ["hourly", "daily", "weekly"] as const;
export const OUTPUT_FILTERS = ["hourly", "daily", "weekly", "monthly", "annual"] as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type Operator = (typeof OPERATORS)[number];
export type TimeStep = (typeof TIME_STEPS)[number];
export type OutputFilter = (typeof OUTPUT_FILTERS)[number];
// ID of a LinkTerm, expecting the "%" separator
export type LinkTermId = `${string}%${string}`;
// ID of a ClusterTerm, expecting the "." separator
export type ClusterTermId = `${string}.${string}`;

export interface LinkTerm {
  id: LinkTermId;
  data: {
    area1: string;
    area2: string;
  };
}

export interface ClusterTerm {
  id: ClusterTermId;
  data: {
    area: string;
    cluster: string;
  };
}

export interface ConstraintTerm {
  id: LinkTermId | ClusterTermId;
  weight: number;
  offset?: number;
  data: LinkTerm["data"] | ClusterTerm["data"];
}

export interface BindingConstraint {
  id: string;
  name: string;
  enabled: boolean;
  timeStep: TimeStep;
  operator: Operator;
  comments?: string;
  filterSynthesis: OutputFilter[];
  filterYearByYear: OutputFilter[];
  terms: ConstraintTerm[];
  // Since v8.7
  group?: string | null;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Checks if the given term data represents a link term.
 *
 * @param termData - The term data to check, which could represent either a link term or a cluster term.
 * @returns True if the term data represents a link term, false otherwise.
 */
export function isLinkTerm(
  termData: LinkTerm["data"] | ClusterTerm["data"],
): termData is LinkTerm["data"] {
  if (!termData) {
    return false;
  }

  if (!("area1" in termData && "area2" in termData)) {
    return false;
  }

  return termData.area1 !== "" && termData.area2 !== "";
}

/**
 * Generates a unique identifier from the given term.
 * The term can be either a link term (2 areas) or a cluster term (area + cluster).
 * For a link term, the identifier format is "area1%area2".
 * For a cluster term, the identifier format is "area.cluster".
 *
 * @param termData - The term data from which to generate the identifier.
 * @returns The generated unique identifier.
 */
export function generateTermId(
  termData: LinkTerm["data"] | ClusterTerm["data"],
): LinkTermId | ClusterTermId {
  if (isLinkTerm(termData)) {
    return `${termData.area1}%${termData.area2}`;
  }
  return `${termData.area}.${termData.cluster}`;
}

/**
 * Checks if a term with the specified ID exists in the list of terms.
 *
 * @param terms - The array of ConstraintTerm objects to search through.
 * @param termId - The unique identifier of the term, either a LinkTermId or a ClusterTermId.
 * @returns True if a term with the specified ID exists; otherwise, false.
 */
export const isTermExist = (terms: ConstraintTerm[], termId: LinkTermId | ClusterTermId): boolean =>
  terms.some(({ id }) => id === termId);

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
  data: string | OutputFilter[] | undefined,
): string | OutputFilter[] {
  // Handle case where the fields are undefined in versions below 8.3.
  if (data === undefined) {
    return [];
  }

  // Handle empty string as an empty array of filters.
  if (typeof data === "string") {
    if (data.length === 0) {
      return [];
    }

    // Convert filters string to array.
    const filtersArray = data.split(/\s*,\s*/);

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
      return data.map((filter) => filter.trim()).join(",");
    } else {
      throw new Error("Array contains invalid output filters values");
    }
  }

  throw new Error("Invalid input: Expected a string or an array of OutputFilter values");
}

/**
 * Adapts fields within a BindingConstraint object to match the expected data formats, facilitating
 * the alignment of API data with UI requirements.
 *
 * @param data - The BindingConstraint object to transform.
 * @returns The transformed BindingConstraint object.
 */
export function bindingConstraintModelAdapter(data: BindingConstraint): BindingConstraint {
  const filterSynthesis = adaptOutputFilterFormat(data.filterSynthesis);
  const filterYearByYear = adaptOutputFilterFormat(data.filterYearByYear);

  return {
    ...data,
    filterSynthesis: filterSynthesis as typeof data.filterSynthesis,
    filterYearByYear: filterYearByYear as typeof data.filterYearByYear,
  };
}
