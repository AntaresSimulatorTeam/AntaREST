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

import { Item } from "@glideapps/glide-data-grid";
import { renderHook } from "@testing-library/react";

import { Column } from "../../../shared/constants";
import type { ColumnType, EnhancedGridColumn } from "../../../shared/types";
import { useColumnMapping } from "..";

export const createCoordinate = (col: number, row: number): Item =>
  [col, row] as Item;

export const createColumn = (
  id: string,
  type: ColumnType,
  editable = false,
): EnhancedGridColumn => ({
  id,
  title: id.charAt(0).toUpperCase() + id.slice(1),
  type,
  width: 100,
  editable,
});

export const createNumericColumn = (id: string) =>
  createColumn(id, Column.Number, true);

export const renderColumnMapping = (columns: EnhancedGridColumn[]) =>
  renderHook(() => useColumnMapping(columns));
