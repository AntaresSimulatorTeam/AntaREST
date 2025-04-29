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

import { isNumericValue } from "@/utils/numberUtils";
import * as R from "ramda";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type SelectionType = "all" | "range" | "advancedRange";

export type Range = [number, number];
export type Selection = number | Range;

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

const SELECTIONS_SEPARATOR = "\n" as const;
export const RANGE_SEPARATOR = "-" as const;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

/**
 * Formalizes the selections by ordering them and merging consecutive numbers.
 *
 * @param selections - An array of numbers and ranges.
 * @returns The formalized selections.
 */
export function formalizeSelections(selections: Selection[]) {
  const numbersSet = new Set<number>();

  selections.forEach((selection) => {
    if (Array.isArray(selection)) {
      const [start, end] = selection;
      for (let i = start; i <= end; i++) {
        numbersSet.add(i);
      }
    } else {
      numbersSet.add(selection);
    }
  });

  const numbersArray = Array.from(numbersSet).sort((a, b) => a - b);

  const formalizeSelections: Selection[] = R.groupWith((a, b) => a + 1 === b, numbersArray).map(
    (group) => (group.length > 1 ? [group[0], group[group.length - 1]] : group[0]),
  );

  return formalizeSelections;
}

export function selectionsToString(selections: Selection[], separator?: string) {
  return selections
    .map((selection) => (Array.isArray(selection) ? selection.join(RANGE_SEPARATOR) : selection))
    .join(separator ?? SELECTIONS_SEPARATOR);
}

export function stringToSelection(selectionString: string) {
  return formalizeSelections(
    selectionString
      .split(SELECTIONS_SEPARATOR)
      .filter(Boolean)
      .map((v) => {
        const [start, end] = v.split(RANGE_SEPARATOR);
        return end ? [Number(start), Number(end)] : Number(start);
      }),
  );
}

export function isSelectionValid(value: string) {
  if (value.includes(RANGE_SEPARATOR)) {
    const splittedValue = value.split(RANGE_SEPARATOR);
    if (splittedValue.length > 2) {
      return false;
    }
    const [start, end] = splittedValue;
    return isNumericValue(start) && isNumericValue(end) && Number(start) <= Number(end);
  }
  return isNumericValue(value);
}
