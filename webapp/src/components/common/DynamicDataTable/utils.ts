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

import type { ChipProps } from "@mui/material";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export enum ColumnOperation {
  SUM = "SUM",
  MAX = "MAX",
  MIN = "MIN",
}

type ColumnResult = Record<string, number>;

export type ChipColorMap = Record<string, ChipProps["color"]>;

export interface Column {
  name: string;
  label: string;
  chipColorMap?: ChipColorMap;
  operation?: ColumnOperation;
}

export type ColumnValues = Record<string, string | number | boolean>;

export interface Item {
  id: string;
  name: string;
  group?: string;
  columns: ColumnValues;
}

export interface AddItemDialogProps {
  open: boolean;
  onClose: () => void;
  onAddItem: (item: Item) => void;
}

////////////////////////////////////////////////////////////////
// Functions
////////////////////////////////////////////////////////////////

export function performColumnOperation(operation: ColumnOperation, values: number[]): number {
  switch (operation) {
    case ColumnOperation.SUM:
      return values.reduce((acc, value) => acc + value, 0);
    case ColumnOperation.MAX:
      return Math.max(...values);
    case ColumnOperation.MIN:
      return Math.min(...values);
    default:
      return 0;
  }
}

export function calculateColumnResults(columns: Column[], items: Item[]): ColumnResult {
  const columnResults: ColumnResult = {};

  columns.forEach((column) => {
    if (column.operation) {
      const values = items
        .filter((item) => item.columns[column.name] !== undefined)
        .map((item) => item.columns[column.name]);

      columnResults[column.name] = performColumnOperation(column.operation, values as number[]);
    }
  });

  return columnResults;
}
