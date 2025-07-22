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

import type { GridCell, Item } from "@glideapps/glide-data-grid";
import type { EnhancedGridColumn, MatrixAggregates } from "../../shared/types";

export type GridToDataFunction = (cell: Item) => Item | null;

export interface UseGridCellContentOptions {
  data: number[][];
  columns: EnhancedGridColumn[];
  gridToData: GridToDataFunction;
  dateTime?: string[];
  aggregates?: MatrixAggregates;
  rowHeaders?: string[];
}

export type CellContentGenerator = (
  row: number,
  col: number,
  column: EnhancedGridColumn,
  data: number[][],
  dateTime?: Date[],
  aggregates?: Partial<MatrixAggregates>,
  rowHeaders?: string[],
) => GridCell;

export interface RenderOptions {
  data: number[][];
  columns: EnhancedGridColumn[];
  dateTime?: string[];
  aggregates?: MatrixAggregates;
  rowHeaders?: string[];
}

export interface TestCase {
  desc: string;
  value: number;
  expected: string;
}
