/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import {
  BaseGridColumn,
  EditableGridCell,
  Item,
} from "@glideapps/glide-data-grid";

////////////////////////////////////////////////////////////////
// Enums
////////////////////////////////////////////////////////////////

export const ColumnTypes = {
  DateTime: "datetime",
  Number: "number",
  Text: "text",
  Aggregate: "aggregate",
} as const;

export const Operations = {
  Add: "+",
  Sub: "-",
  Mul: "*",
  Div: "/",
  Abs: "ABS",
  Eq: "=",
} as const;

// !NOTE: Keep lowercase to match Glide Data Grid column ids
export const Aggregates = {
  Min: "min",
  Max: "max",
  Avg: "avg",
  Total: "total",
} as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

// Derived types
export type ColumnType = (typeof ColumnTypes)[keyof typeof ColumnTypes];
export type Operation = (typeof Operations)[keyof typeof Operations];

export interface TimeSeriesColumnOptions {
  count: number;
  startIndex?: number;
  prefix?: string;
  width?: number;
  editable?: boolean;
  style?: BaseGridColumn["style"];
}

export interface CustomColumnOptions {
  titles: string[] | readonly string[];
  width?: number;
}

export interface EnhancedGridColumn extends BaseGridColumn {
  id: string;
  width?: number;
  type: ColumnType;
  editable: boolean;
}

export type AggregateType = (typeof Aggregates)[keyof typeof Aggregates];
export type AggregateConfig = AggregateType[] | boolean | "stats" | "all";

export interface MatrixAggregates {
  min: number[];
  max: number[];
  avg: number[];
  total: number[];
}

// Represents data coming from the API
export interface MatrixDataDTO {
  data: number[][];
  columns: number[];
  index: number[];
}

export type Coordinates = [number, number];

// Shape of updates provided by Glide Data Grid
export interface GridUpdate {
  coordinates: Item; // The cell being updated
  value: EditableGridCell;
}

// Shape of updates to be sent to the API
export interface MatrixUpdate {
  operation: Operation;
  value: number;
}

// Shape of multiple updates to be sent to the API
export interface MatrixUpdateDTO {
  coordinates: number[][]; // Array of [col, row] pairs
  operation: MatrixUpdate;
}

export type DateIncrementStrategy = (
  date: moment.Moment,
  step: number,
) => moment.Moment;
