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
import type { FilterState } from "./types";

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
