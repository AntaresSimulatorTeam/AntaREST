/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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
import * as RA from "ramda-adjunct";
import { isNumericValue } from "./numberUtils";

export type Range = [number, number];
export type NumberOrRange = number | Range;

export const SELECTIONS_SEPARATOR = "," as const;
export const RANGE_SEPARATOR = "-" as const;

/**
 * Converts a number or a range into an array of numbers.
 *
 * @example
 * selectionToNumbers(8); // Returns: [8]
 * selectionToNumbers([4, 6]); // Returns: [4, 5, 6]
 *
 * @param selection - A number or a range.
 * @returns An array of numbers.
 */
export function selectionToNumbers(selection: NumberOrRange) {
  if (Array.isArray(selection)) {
    const [start, end] = selection;
    return R.range(start, end + 1);
  }
  return [selection];
}

/**
 * Converts an array of numbers and/or ranges into a sorted array of unique numbers.
 *
 * @example
 * selectionsToNumbers([8, 1, 2, [4, 6], 3]); // Returns: [1, 2, 3, 4, 5, 6, 8]
 *
 * @param selections - An array of numbers and/or ranges.
 * @returns A sorted array of unique numbers.
 */
export function selectionsToNumbers(selections: NumberOrRange[]) {
  const numbersSet = new Set<number>();

  selections.forEach((selection) => {
    selectionToNumbers(selection).forEach((num) => {
      numbersSet.add(num);
    });
  });

  return Array.from(numbersSet).sort((a, b) => a - b);
}

/**
 * Compacts an array of numbers and/or ranges by sorting and merging consecutive numbers into ranges.
 *
 * @example
 * compactSelections([8, 1, 2, [4, 6], 3]); // Returns: [[1, 6], 8]
 *
 * @param selections - An array of numbers and/or ranges.
 * @returns A compacted array of numbers and/or ranges, sorted and merged.
 */
export function compactSelections(selections: NumberOrRange[]) {
  const compacted: NumberOrRange[] = R.groupWith(
    (a, b) => a + 1 === b,
    selectionsToNumbers(selections),
  ).map((group) => (group.length > 1 ? [group[0], group[group.length - 1]] : group[0]));

  return compacted;
}

/**
 * Converts a number or a range into its string representation.
 *
 * @example
 * selectionToString(8); // Returns: "8"
 * selectionToString([1, 8]); // Returns: "1-8"
 *
 * @param selection - A number or a range.
 * @returns A string representation of the selection.
 */
export function selectionToString(selection: NumberOrRange) {
  return Array.isArray(selection) ? selection.join(RANGE_SEPARATOR) : selection.toString();
}

/**
 * Converts an array of numbers and/or ranges into a string representation.
 *
 * @example
 * selectionsToString([8, 1, 2, [4, 6]]); // Returns: "8, 1, 2, 4-6"
 *
 * @param selections - An array of numbers and/or ranges.
 * @returns A string representation of the selections.
 */
export function selectionsToString(selections: NumberOrRange[]) {
  return selections.map(selectionToString).join(SELECTIONS_SEPARATOR + " ");
}

/**
 * Converts a string representation of selections of numbers and/or ranges
 * into an array of numbers and/or ranges.
 *
 * @example
 * stringToSelections("8, 1, 2, 4-6, 3"); // Returns: [8, 1, 2, [4, 6], 3]
 *
 * @param selectionString - A string representation of selections.
 * @returns An array of numbers and/or ranges.
 */
export function stringToSelections(selectionString: string) {
  const selections: NumberOrRange[] = selectionString
    .split(SELECTIONS_SEPARATOR)
    .map((v) => v.trim())
    .filter(Boolean)
    .map((v) => {
      const [start, end] = v.split(RANGE_SEPARATOR);
      return end ? [Number(start), Number(end)] : Number(start);
    });

  return selections;
}

/**
 * Checks if a selection (number or range, or a string representation of either) is valid.
 *
 * @see {@link isNumericValue} For checking if a value is numeric.
 *
 * @example
 * isSelectionValid("8", 10); // Returns: `true`
 * isSelectionValid("1-10", 10); // Returns: `true`
 * isSelectionValid("1-11", 10); // Returns: `false`
 * isSelectionValid("foo", 10); // Returns: `false`
 *
 * @param value - A selection.
 * @param maxValue - The maximum allowed value for the selection.
 * @returns `true` if the selection is valid, `false` otherwise.
 */
export function isSelectionValid(value: string | NumberOrRange, maxValue: number) {
  if (typeof value !== "string") {
    return isSelectionValid(selectionToString(value), maxValue);
  }

  if (value.includes(RANGE_SEPARATOR)) {
    const splittedValue = value.split(RANGE_SEPARATOR);

    if (splittedValue.length > 2) {
      return false;
    }

    const [start, end] = splittedValue;

    return (
      isNumericValue(start) &&
      isNumericValue(end) &&
      Number(start) <= Number(end) &&
      Number(start) >= 1 &&
      Number(end) <= maxValue
    );
  }

  return isNumericValue(value) && RA.inRange(1, maxValue + 1, Number(value));
}

/**
 * Checks if selections (numbers and/or ranges, or a string representation of them) is valid.
 *
 * @see {@link isSelectionValid}
 *
 * @example
 * isSelectionsValid("8, 1-4, 9", 10); // Returns: `true`
 * isSelectionsValid("1-5, 11", 10); // Returns: `false`
 *
 * @param value - The selections.
 * @param maxValue - The maximum allowed value for the selections.
 * @returns `true` if the selections are valid, `false` otherwise.
 */
export function isSelectionsValid(value: string | NumberOrRange[], maxValue: number) {
  if (typeof value !== "string") {
    return isSelectionsValid(selectionsToString(value), maxValue);
  }

  const trimmedValue = value.trim();

  return (
    trimmedValue === "" ||
    R.all((str) => isSelectionValid(str, maxValue), trimmedValue.split(SELECTIONS_SEPARATOR))
  );
}
