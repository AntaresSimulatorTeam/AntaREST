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

import { HOURS_IN } from "@/utils/date/constants";
import * as R from "ramda";
import type { ConstraintValues } from "../../utils";

export type RowData = Record<string, boolean>;

export type OccurrencesData = Record<string, RowData>;

export const resizeRow = R.curry((resizeValue: number, rowData: RowData) => {
  const indexes = R.range(0, resizeValue);
  const values = R.map((i) => rowData[i] || false, indexes);
  return R.zipObj(indexes, values);
});

export const occurrencesToGridData = (occurrences: ConstraintValues["occurrences"]) => {
  const data: OccurrencesData = {};

  for (let hour = 1; hour <= HOURS_IN.WEEK; hour++) {
    const rowData: RowData = {};

    occurrences.forEach(({ hours }, index) => {
      rowData[index] = hours.includes(hour);
    });

    data[hour] = rowData;
  }

  return data;
};

export const gridDataToOccurrences = (data: OccurrencesData): ConstraintValues["occurrences"] => {
  return Object.entries(data).reduce<ConstraintValues["occurrences"]>(
    (occurrencesAcc, [hour, rowData]) => {
      Object.values(rowData).forEach((active, i) => {
        occurrencesAcc[i] ??= { hours: [] };
        if (active) {
          occurrencesAcc[i].hours.push(Number(hour));
        }
      });

      return occurrencesAcc;
    },
    [],
  );
};

export function getSelectedHoursByOccurrence({
  hours,
  occurrences,
  offset,
}: {
  hours: number[];
  occurrences: number;
  offset: number;
}) {
  // Hour elections are only applied to the first occurrence
  if (offset === 0) {
    return [hours];
  }

  return Array.from({ length: occurrences }, (_, occurrenceIndex) => {
    const shift = occurrenceIndex * offset;

    // `hour - 1`: Converts 1-based hour to 0-based for modulo arithmetic.
    // `+ shift`: Applies the total offset for this occurrence.
    // `% HOURS_IN.WEEK`: Wraps around if the result exceeds the number of hours in a week.
    // `+ 1`: Converts back to 1-based hour.
    const applyOffset = (hour: number) => ((hour - 1 + shift) % HOURS_IN.WEEK) + 1;

    return hours
      .map((selection) => {
        const nextHour = applyOffset(selection);

        if (nextHour > HOURS_IN.WEEK) {
          return nextHour - HOURS_IN.WEEK;
        }

        return nextHour;
      })
      .sort((a, b) => a - b);
  });
}
