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

import * as R from "ramda";
import type { FilterCriteria } from "../types";

/**
 * Efficiently compares two arrays of numbers for equality using
 * Ramda's equals uses fast-path optimizations for arrays
 *
 * @param arr1
 * @param arr2
 */
export const areArraysEqual = R.equals<number[]>;

/**
 * Compares two FilterCriteria objects for equality
 *
 * @param criteria1
 * @param criteria2
 */
export const areFilterCriteriaEqual = R.equals<FilterCriteria | null>;

/**
 * Creates a memoization key from filter criteria
 *
 * @param criteria - The filter criteria containing columns and rows indices
 * @returns A string key for memoization purposes
 */
export const getFilterCriteriaKey = (criteria: FilterCriteria): string => {
  const { columnsIndices, rowsIndices } = criteria;

  // Use simple key for small arrays
  if (columnsIndices.length <= 10 && rowsIndices.length <= 10) {
    return `c:${R.join(",", columnsIndices)}_r:${R.join(",", rowsIndices)}`;
  }

  // Use length and samples for larger arrays
  const createSample = (arr: number[]): number[] => {
    const first5 = R.take(5, arr);
    const last5 = R.takeLast(5, arr);
    return R.uniq(R.concat(first5, last5));
  };

  const colSample = createSample(columnsIndices);
  const rowSample = createSample(rowsIndices);

  return `c:${columnsIndices.length}[${colSample}]_r:${rowsIndices.length}[${rowSample}]`;
};

/**
 * Shallow compares two objects excluding specified keys using Ramda
 *
 * @param obj1 - The first object to compare
 * @param obj2 - The second object to compare
 * @param excludeKeys - Array of keys to exclude from comparison
 * @returns True if objects are equal after excluding specified keys, false otherwise
 */
export const shallowCompareExcept = <T extends Record<string, unknown>>(
  obj1: T,
  obj2: T,
  excludeKeys: readonly string[] = [],
): boolean => {
  const omitKeys = R.omit(excludeKeys as string[]) as (obj: T) => Partial<T>;
  return R.equals(omitKeys(obj1), omitKeys(obj2));
};
