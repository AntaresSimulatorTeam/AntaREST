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

import type { ColumnType, EnhancedGridColumn } from "../../../shared/types";
import { Column, TimeFrequency } from "../../../shared/constants";
import type { TestCase } from "../types";
import { UTCDate } from "@date-fns/utc";

export const createColumn = (
  id: string,
  type: ColumnType,
  editable = false,
): EnhancedGridColumn => ({
  id,
  title: id.charAt(0).toUpperCase() + id.slice(1),
  type,
  width: type === Column.DateTime ? 150 : 50,
  editable,
});

export const AGGREGATE_DATA = {
  columns: [createColumn("total", Column.Aggregate)],
  data: [
    [10, 20, 30],
    [15, 25, 35],
    [5, 15, 25],
  ],
  aggregates: {
    min: [5, 15, 25],
    max: [15, 25, 35],
    avg: [10, 20, 30],
    total: [30, 60, 90],
  },
};

export const MIXED_DATA = {
  columns: [
    createColumn("rowHeader", Column.Text),
    createColumn("date", Column.DateTime),
    createColumn("data1", Column.Number, true),
    createColumn("data2", Column.Number, true),
    createColumn("total", Column.Aggregate),
  ],
  data: [
    [100, 200],
    [150, 250],
  ],
  dateTime: {
    values: [new UTCDate("2024-01-01T00:00:00Z"), new UTCDate("2024-01-02T00:00:00Z")],
    first_week_size: 7,
    level: TimeFrequency.Daily,
  },
  rowHeaders: ["Row 1", "Row 2"],
  aggregates: {
    min: [100, 200],
    max: [150, 250],
    avg: [125, 225],
    total: [250, 450],
  },
};

export const EDGE_CASES = {
  emptyData: {
    columns: [createColumn("data1", Column.Number, true)],
    data: [],
  },
  singleCell: {
    columns: [createColumn("data1", Column.Number, true)],
    data: [[100]],
  },
};

export const FORMAT_TEST_CASES: TestCase[] = [
  {
    desc: "formats regular numbers",
    value: 1234567.89,
    expected: "1 234 567.89",
  },
  {
    desc: "handles very large numbers",
    value: 1e20,
    expected: "100 000 000 000 000 000 000",
  },
  {
    desc: "handles very small numbers",
    value: 0.00001,
    expected: "0.00001",
  },
  {
    desc: "handles negative numbers",
    value: -1234567.89,
    expected: "-1 234 567.89",
  },
  {
    desc: "handles zero",
    value: 0,
    expected: "0",
  },
];
