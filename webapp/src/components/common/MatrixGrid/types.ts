/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
  ADD: "+",
  SUB: "-",
  MUL: "*",
  DIV: "/",
  ABS: "ABS",
  EQ: "=",
} as const;

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

// Derived types
export type ColumnType = (typeof ColumnTypes)[keyof typeof ColumnTypes];
export type Operation = (typeof Operations)[keyof typeof Operations];

export interface EnhancedGridColumn extends BaseGridColumn {
  id: string;
  width?: number;
  type: ColumnType;
  editable: boolean;
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
