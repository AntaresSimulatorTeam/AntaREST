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

import { Aggregate, TimeFrequency } from "../constants";
import type { FormatTestCase } from "./types";

export const BASE_DATA = {
  dateConfig: {
    start_date: "2023-01-01 00:00:00",
    steps: 3,
    first_week_size: 7,
  },
  matrix: [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
  ],
};

export const DATE_TIME_TEST_CASES = [
  {
    name: "annual format",
    config: { ...BASE_DATA.dateConfig, level: TimeFrequency.Annual },
    expected: ["global.time.annual", "global.time.annual", "global.time.annual"],
  },
  {
    name: "monthly format",
    config: { ...BASE_DATA.dateConfig, level: TimeFrequency.Monthly },
    expected: ["Jan", "Feb", "Mar"],
  },
  {
    name: "weekly format",
    config: {
      ...BASE_DATA.dateConfig,
      level: TimeFrequency.Weekly,
      first_week_size: 1,
    },
    expected: ["global.time.weekShort 01", "global.time.weekShort 02", "global.time.weekShort 03"],
  },
  {
    name: "daily format",
    config: { ...BASE_DATA.dateConfig, level: TimeFrequency.Daily },
    expected: ["Sun 1 Jan", "Mon 2 Jan", "Tue 3 Jan"],
  },
  {
    name: "hourly format",
    config: {
      start_date: "2039-07-01 00:00:00",
      steps: 3,
      first_week_size: 7,
      level: TimeFrequency.Hourly,
    },
    expected: ["Fri 1 Jul 00:00", "Fri 1 Jul 01:00", "Fri 1 Jul 02:00"],
  },
];

export const COLUMN_TEST_CASES = [
  {
    name: "default options",
    input: { count: 3 },
    expectedLength: 3,
  },
  {
    name: "custom options",
    input: { count: 2, startIndex: 10, prefix: "Data", editable: false },
    expectedLength: 2,
  },
  {
    name: "zero count",
    input: { count: 0 },
    expectedLength: 0,
  },
  {
    name: "large count",
    input: { count: 1000 },
    expectedLength: 1000,
  },
];

export const AGGREGATE_TEST_CASES = [
  {
    name: "simple matrix with all aggregates",
    matrix: BASE_DATA.matrix,
    aggregates: "all" as const,
    expected: {
      min: [1, 4, 7],
      max: [3, 6, 9],
      avg: [2, 5, 8],
      total: [6, 15, 24],
    },
  },
  {
    name: "decimal numbers",
    matrix: [
      [1.1, 2.2, 3.3],
      [4.4, 5.5, 6.6],
    ],
    aggregates: "all" as const,
    expected: {
      min: [1.1, 4.4],
      max: [3.3, 6.6],
      avg: [2, 6],
      total: [7, 17],
    },
  },
  {
    name: "negative numbers",
    matrix: [
      [-1, -2, -3],
      [-4, 0, 4],
    ],
    aggregates: "all" as const,
    expected: {
      min: [-3, -4],
      max: [-1, 4],
      avg: [-2, 0],
      total: [-6, 0],
    },
  },
];

export const FORMAT_TEST_CASES: Array<{
  name: string;
  cases: FormatTestCase[];
}> = [
  {
    name: "integer numbers",
    cases: [
      {
        description: "formats large number",
        value: 1234567,
        expected: "1 234 567",
      },
      {
        description: "formats million",
        value: 1000000,
        expected: "1 000 000",
      },
      { description: "formats single digit", value: 1, expected: "1" },
    ],
  },
  {
    name: "decimal numbers",
    cases: [
      {
        description: "formats with 2 decimals",
        value: 1234.56,
        maxDecimals: 2,
        expected: "1 234.56",
      },
      {
        description: "formats with 3 decimals",
        value: 1000000.123,
        maxDecimals: 3,
        expected: "1 000 000.123",
      },
    ],
  },
  {
    name: "special cases",
    cases: [
      {
        description: "handles undefined",
        value: undefined,
        maxDecimals: 3,
        expected: "",
      },
      { description: "handles zero", value: 0, expected: "0" },
      {
        description: "handles negative",
        value: -1234567,
        expected: "-1 234 567",
      },
      {
        description: "handles very large number",
        value: 1e20,
        expected: "100 000 000 000 000 000 000",
      },
    ],
  },
];

export const AGGREGATE_CONFIG_CASES = [
  {
    name: "stats configuration",
    aggregates: "stats" as const,
    expected: [Aggregate.Avg, Aggregate.Min, Aggregate.Max],
  },
  {
    name: "all configuration",
    aggregates: "all" as const,
    expected: [Aggregate.Min, Aggregate.Max, Aggregate.Avg, Aggregate.Total],
  },
  {
    name: "custom configuration",
    aggregates: [Aggregate.Min, Aggregate.Max],
    expected: [Aggregate.Min, Aggregate.Max],
  },
];
