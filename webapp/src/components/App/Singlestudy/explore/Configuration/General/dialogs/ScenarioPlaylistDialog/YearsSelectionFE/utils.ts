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
import * as RA from "ramda-adjunct";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type Range = [number, number];
export type Selection = number | Range;

////////////////////////////////////////////////////////////////
// Constants
////////////////////////////////////////////////////////////////

export const SELECTIONS_SEPARATOR = "," as const;
export const RANGE_SEPARATOR = "-" as const;

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function selectionsToNumbers(selections: Selection[]) {
  const numbersSet = new Set<number>();

  selections.forEach((selection) => {
    if (Array.isArray(selection)) {
      const [start, end] = selection;
      R.range(start, end + 1).forEach((num) => numbersSet.add(num));
    } else {
      numbersSet.add(selection);
    }
  });

  return Array.from(numbersSet).sort((a, b) => a - b);
}

/**
 * Formalizes the selections by ordering them and merging consecutive numbers.
 *
 * @param selections - An array of numbers and ranges.
 * @returns The formalized selections.
 */
function formalizeSelections(selections: Selection[]) {
  const formalizeSelections: Selection[] = R.groupWith(
    (a, b) => a + 1 === b,
    selectionsToNumbers(selections),
  ).map((group) => (group.length > 1 ? [group[0], group[group.length - 1]] : group[0]));

  return formalizeSelections;
}

export function selectionsToString(selections: Selection[]) {
  return selections
    .map((selection) => (Array.isArray(selection) ? selection.join(RANGE_SEPARATOR) : selection))
    .join(SELECTIONS_SEPARATOR + " ");
}

export function stringToSelection(selectionString: string) {
  return formalizeSelections(
    selectionString
      .split(SELECTIONS_SEPARATOR)
      .map((v) => v.trim())
      .filter(Boolean)
      .map((v) => {
        const [start, end] = v.split(RANGE_SEPARATOR);
        return end ? [Number(start), Number(end)] : Number(start);
      }),
  );
}

function isSelectionValid(value: string, maxValue: number) {
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

export function isSelectionsValid(value: string, maxValue: number) {
  const trimmedValue = value.trim();

  return (
    trimmedValue === "" ||
    R.all((str) => isSelectionValid(str, maxValue), trimmedValue.split(SELECTIONS_SEPARATOR))
  );
}
