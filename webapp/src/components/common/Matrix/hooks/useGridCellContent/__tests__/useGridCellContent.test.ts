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

import { Column } from "../../../shared/constants";
import { createColumn, AGGREGATE_DATA, MIXED_DATA, FORMAT_TEST_CASES } from "./fixtures";
import { createCoordinate, renderGridCellContent } from "./utils";
import { assertNumberCell, assertTextCell } from "./assertions";

describe("useGridCellContent", () => {
  describe("Aggregate columns", () => {
    test.each([
      [0, 30],
      [1, 60],
      [2, 90],
    ])("returns correct aggregate for row %i", (row, expected) => {
      const getCellContent = renderGridCellContent(AGGREGATE_DATA);
      const cell = getCellContent(createCoordinate(0, row));
      assertNumberCell(cell, expected, `Expected aggregate value ${expected} at row ${row}`);
    });
  });

  describe("Mixed column types", () => {
    test("handles all column types correctly", () => {
      const getCellContent = renderGridCellContent(MIXED_DATA);

      assertTextCell(getCellContent(createCoordinate(0, 0)), "Row 1", "Expected row header text");

      assertNumberCell(
        getCellContent(createCoordinate(2, 0)),
        100,
        "Expected first data column value",
      );

      assertNumberCell(
        getCellContent(createCoordinate(3, 0)),
        200,
        "Expected second data column value",
      );

      assertNumberCell(getCellContent(createCoordinate(4, 0)), 250, "Expected aggregate value");
    });
  });

  describe("Edge cases", () => {
    test("handles empty data array", () => {
      const options = {
        columns: [createColumn("data1", Column.Number, true)],
        data: [],
      };

      const getCellContent = renderGridCellContent(options);
      const cell = getCellContent(createCoordinate(0, 0));
      assertNumberCell(cell, undefined, "Expected undefined for empty data");
    });

    test("handles out of bounds access", () => {
      const options = {
        columns: [createColumn("data1", Column.Number, true)],
        data: [[100]],
      };

      const getCellContent = renderGridCellContent(options);

      // Column out of bounds
      const colCell = getCellContent(createCoordinate(1, 0));
      assertTextCell(colCell, "N/A", "Expected N/A for column out of bounds");

      // Row out of bounds
      const rowCell = getCellContent(createCoordinate(0, 1));
      assertNumberCell(rowCell, undefined, "Expected undefined for row out of bounds");
    });
  });

  describe("Number formatting", () => {
    test.each(FORMAT_TEST_CASES)("$desc", ({ value, expected }) => {
      const options = {
        columns: [createColumn("number", Column.Number, true)],
        data: [[value]],
      };

      const getCellContent = renderGridCellContent(options);
      const cell = getCellContent(createCoordinate(0, 0));

      if (cell.kind === "number" && "data" in cell) {
        expect(cell.data).toBe(value);
        expect(cell.displayData).toBe(expected);
      } else {
        throw new Error(`Expected formatted number cell for value ${value}`);
      }
    });
  });
});
