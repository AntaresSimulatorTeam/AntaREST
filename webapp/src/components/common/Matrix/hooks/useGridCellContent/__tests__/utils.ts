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

import { renderHook } from "@testing-library/react";
import type { Item } from "@glideapps/glide-data-grid";
import { useColumnMapping } from "../../useColumnMapping";
import { useGridCellContent } from "..";
import type { RenderOptions } from "../types";

export const createCoordinate = (col: number, row: number): Item => [col, row] as Item;

export const renderGridCellContent = ({
  data,
  columns,
  dateTime,
  aggregates,
  rowHeaders,
}: RenderOptions) => {
  const { result: mappingResult } = renderHook(() => useColumnMapping(columns));

  const { gridToData } = mappingResult.current;

  const { result } = renderHook(() =>
    useGridCellContent(data, columns, gridToData, dateTime, aggregates, rowHeaders),
  );

  return result.current;
};
