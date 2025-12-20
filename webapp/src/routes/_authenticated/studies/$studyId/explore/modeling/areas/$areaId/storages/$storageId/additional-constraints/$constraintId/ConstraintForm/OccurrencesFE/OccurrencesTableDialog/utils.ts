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

import type { AdditionalConstraintOccurrences } from "@/services/api/studies/areas/storages/types";
import { HOURS_IN } from "@/utils/date/constants";
import * as R from "ramda";

export type RowData = Record<string, boolean>;

export type OccurrencesData = Record<string, RowData>;

export const resizeRow = R.curry((resizeValue: number, rowData: RowData) => {
  const indexes = R.range(0, resizeValue);
  const values = R.map((i) => rowData[i] || false, indexes);
  return R.zipObj(indexes, values);
});

export const occurrencesToGridData = (occurrences: AdditionalConstraintOccurrences) => {
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

export const getOccurrencesCountFromGridData = (data: OccurrencesData) => {
  const row = Object.values(data)[0] || {};
  return Object.keys(row).length;
};

export const gridDataToOccurrences = (data: OccurrencesData): AdditionalConstraintOccurrences => {
  // `OccurrencesData` and `RowData` use integer keys, so order is guaranteed
  // when using `Object.entries` and `Object.values`
  return Object.entries(data).reduce<AdditionalConstraintOccurrences>(
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
  occurrencesCount,
  offset,
}: {
  hours: number[];
  occurrencesCount: number;
  offset: number;
}) {
  // Only applied to the first occurrence
  if (offset === 0) {
    return [hours];
  }

  return Array.from({ length: occurrencesCount }, (_, occurrenceIndex) => {
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
