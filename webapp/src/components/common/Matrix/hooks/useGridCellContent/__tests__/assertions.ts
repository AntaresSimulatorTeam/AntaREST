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

import { GridCell } from "@glideapps/glide-data-grid";

export const assertNumberCell = (
  cell: GridCell,
  expectedValue: number | undefined,
  message: string,
) => {
  if (cell.kind === "number" && "data" in cell) {
    expect(cell.data).toBe(expectedValue);
  } else {
    throw new Error(message);
  }
};

export const assertTextCell = (
  cell: GridCell,
  expectedValue: string,
  message: string,
) => {
  if (cell.kind === "text" && "displayData" in cell) {
    expect(cell.displayData).toBe(expectedValue);
  } else {
    throw new Error(message);
  }
};

export const assertDateCell = (
  cell: GridCell,
  expectedValue: string,
  message: string,
) => {
  if (cell.kind === "text" && "displayData" in cell) {
    expect(cell.displayData).toBe(expectedValue);
  } else {
    throw new Error(message);
  }
};
