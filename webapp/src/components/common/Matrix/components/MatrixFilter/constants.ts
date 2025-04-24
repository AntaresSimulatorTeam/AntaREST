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

import { Operation } from "../../shared/constants";
import type { FilterState, TemporalOption } from "./types";

export const FILTER_TYPES = {
  RANGE: "range",
  MODULO: "modulo",
  LIST: "list",
};

export const TIME_INDEXING = {
  DAY_OF_MONTH: "dayOfMonth",
  DAY_OF_YEAR: "dayOfYear",
  DAY_HOUR: "dayHour",
  HOUR_YEAR: "hourYear",
  MONTH: "month",
  WEEK: "week",
  WEEKDAY: "weekday",
};

export const TEMPORAL_OPTIONS: TemporalOption[] = [
  {
    value: TIME_INDEXING.DAY_OF_MONTH,
    label: "matrix.filter.indexing.dayOfMonth",
    description: "Filter by day of month (1-31)",
  },
  {
    value: TIME_INDEXING.MONTH,
    label: "matrix.filter.indexing.month",
    description: "Filter by month (1-12)",
  },
  {
    value: TIME_INDEXING.WEEKDAY,
    label: "matrix.filter.indexing.weekday",
    description: "Filter by weekday (1-7, Monday to Sunday)",
  },
  {
    value: TIME_INDEXING.DAY_HOUR,
    label: "matrix.filter.indexing.dayHour",
    description: "Filter by hour of day (1-24)",
  },
  {
    value: TIME_INDEXING.WEEK,
    label: "matrix.filter.indexing.week",
    description: "Filter by week of year (1-53)",
  },
  {
    value: TIME_INDEXING.DAY_OF_YEAR,
    label: "matrix.filter.indexing.dayOfYear",
    description: "Filter by day of year (1-366)",
  },
  {
    value: TIME_INDEXING.HOUR_YEAR,
    label: "matrix.filter.indexing.hourYear",
    description: "Filter by hour of year (1-8760)",
  },
];

export const getDefaultFilterState = (rowCount: number, columnCount: number): FilterState => ({
  active: false,
  columnsFilter: {
    type: FILTER_TYPES.RANGE,
    range: { min: 1, max: columnCount || 1 },
  },
  rowsFilter: {
    indexingType: TIME_INDEXING.DAY_OF_MONTH,
    type: FILTER_TYPES.RANGE,
    range: { min: 1, max: rowCount || 1 },
  },
  operation: {
    type: Operation.Eq,
    value: 0,
  },
});
