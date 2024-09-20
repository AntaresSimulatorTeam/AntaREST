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

import { renderHook } from "@testing-library/react";
import { useGridCellContent } from "./useGridCellContent";
import { ColumnTypes, type EnhancedGridColumn } from "./types";
import { useColumnMapping } from "./useColumnMapping";

// Mocking i18next
vi.mock("i18next", () => {
  const i18n = {
    language: "fr",
    use: vi.fn().mockReturnThis(),
    init: vi.fn(),
    t: vi.fn((key) => key),
    changeLanguage: vi.fn((lang) => {
      i18n.language = lang;
      return Promise.resolve();
    }),
    on: vi.fn(),
  };
  return { default: i18n };
});

// Mocking react-i18next
vi.mock("react-i18next", async (importOriginal) => {
  const actual = await importOriginal();
  return Object.assign({}, actual, {
    useTranslation: () => ({
      t: vi.fn((key) => key),
      i18n: {
        changeLanguage: vi.fn(),
        language: "fr",
      },
    }),
    initReactI18next: {
      type: "3rdParty",
      init: vi.fn(),
    },
  });
});

function renderGridCellContent(
  data: number[][],
  columns: EnhancedGridColumn[],
  dateTime?: string[],
  aggregates?: Record<string, number[]>,
  rowHeaders?: string[],
) {
  const { result: mappingResult } = renderHook(() => useColumnMapping(columns));
  const { gridToData } = mappingResult.current;

  const { result } = renderHook(() =>
    useGridCellContent(
      data,
      columns,
      gridToData,
      dateTime,
      aggregates,
      rowHeaders,
    ),
  );

  return result.current;
}

describe("useGridCellContent", () => {
  test("returns correct text cell content for DateTime columns", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "date",
        title: "Date",
        type: ColumnTypes.DateTime,
        width: 150,
        editable: false,
      },
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];

    const dateTime = ["2024-01-07T00:00:00Z", "2024-01-02T00:00:00Z"];

    const data = [
      [11, 10],
      [12, 15],
    ];

    const getCellContent = renderGridCellContent(data, columns, dateTime);
    const cell = getCellContent([0, 0]);

    if ("displayData" in cell) {
      expect(cell.kind).toBe("text");
      expect(cell.displayData).toBe("7 janv. 2024, 00:00");
    } else {
      throw new Error("Expected a text cell with displayData");
    }
  });

  describe("returns correct cell content for Aggregate columns", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "total",
        title: "Total",
        type: ColumnTypes.Aggregate,
        width: 100,
        editable: false,
      },
    ];

    const data = [
      [10, 20, 30],
      [15, 25, 35],
      [5, 15, 25],
    ];

    const aggregates = {
      total: [60, 75, 45],
    };

    // Tests for each row in the aggregates array
    test.each([
      [0, 60], // Row index 0, expected sum 60
      [1, 75], // Row index 1, expected sum 75
      [2, 45], // Row index 2, expected sum 45
    ])(
      "ensures the correct numeric cell content is returned for aggregates at row %i",
      (row, expectedData) => {
        const getCellContent = renderGridCellContent(
          data,
          columns,
          undefined,
          aggregates,
        );

        const cell = getCellContent([0, row]); // Column index is 0 because we only have one column of aggregates

        if ("data" in cell) {
          expect(cell.kind).toBe("number");
          expect(cell.data).toBe(expectedData);
        } else {
          throw new Error(`Expected a number cell with data at row [${row}]`);
        }
      },
    );
  });

  test("returns correct content for DateTime, Number, and Aggregate columns", () => {
    const columns = [
      {
        id: "date",
        title: "Date",
        type: ColumnTypes.DateTime,
        width: 150,
        editable: false,
      },
      {
        id: "ts1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "ts2",
        title: "TS 2",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "total",
        title: "Total",
        type: ColumnTypes.Aggregate,
        width: 100,
        editable: false,
      },
    ];

    const dateTime = ["2021-01-01T00:00:00Z", "2021-01-02T00:00:00Z"];

    const data = [
      [100, 200],
      [150, 250],
    ];

    const aggregates = {
      total: [300, 400],
    };

    const getCellContent = renderGridCellContent(
      data,
      columns,
      dateTime,
      aggregates,
    );

    const dateTimeCell = getCellContent([0, 0]);

    if (dateTimeCell.kind === "text" && "displayData" in dateTimeCell) {
      expect(dateTimeCell.data).toBe("");
      expect(dateTimeCell.displayData).toBe("1 janv. 2021, 00:00");
    } else {
      throw new Error(
        "Expected a DateTime cell with displayData containing the year 2021",
      );
    }

    const numberCell = getCellContent([1, 0]);

    if (numberCell.kind === "number" && "data" in numberCell) {
      expect(numberCell.data).toBe(100);
    } else {
      throw new Error("Expected a Number cell with data");
    }

    const aggregateCell = getCellContent([3, 0]);

    if (aggregateCell.kind === "number" && "data" in aggregateCell) {
      expect(aggregateCell.data).toBe(300);
    } else {
      throw new Error("Expected an Aggregate cell with data");
    }
  });
});

describe("useGridCellContent with mixed column types", () => {
  test("handles non-data columns correctly and accesses data columns properly", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "rowHeader",
        title: "Row",
        type: ColumnTypes.Text,
        width: 100,
        editable: false,
      },
      {
        id: "date",
        title: "Date",
        type: ColumnTypes.DateTime,
        width: 150,
        editable: false,
      },
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "data2",
        title: "TS 2",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "total",
        title: "Total",
        type: ColumnTypes.Aggregate,
        width: 100,
        editable: false,
      },
    ];

    const rowHeaders = ["Row 1", "Row 2"];
    const dateTime = ["2024-01-01T00:00:00Z", "2024-01-02T00:00:00Z"];
    const data = [
      [100, 200],
      [150, 250],
    ];
    const aggregates = {
      total: [300, 400],
    };

    const getCellContent = renderGridCellContent(
      data,
      columns,
      dateTime,
      aggregates,
      rowHeaders,
    );

    // Test row header (Text column)
    const rowHeaderCell = getCellContent([0, 0]);

    if (rowHeaderCell.kind === "text" && "displayData" in rowHeaderCell) {
      expect(rowHeaderCell.displayData).toBe("Row 1");
    } else {
      throw new Error("Expected a text cell with data for row header");
    }

    // Test date column (DateTime column)
    const dateCell = getCellContent([1, 0]);
    if (dateCell.kind === "text" && "displayData" in dateCell) {
      expect(dateCell.data).toBe("");
      expect(dateCell.displayData).toBe("1 janv. 2024, 00:00");
    } else {
      throw new Error("Expected a text cell with data for date");
    }

    // Test first data column (Number column)
    const firstDataCell = getCellContent([2, 0]);

    if (firstDataCell.kind === "number" && "data" in firstDataCell) {
      expect(firstDataCell.data).toBe(100);
    } else {
      throw new Error("Expected a number cell with data for first data column");
    }

    // Test second data column (Number column)
    const secondDataCell = getCellContent([3, 0]);

    if (secondDataCell.kind === "number" && "data" in secondDataCell) {
      expect(secondDataCell.data).toBe(200);
    } else {
      throw new Error(
        "Expected a number cell with data for second data column",
      );
    }

    // Test aggregate column
    const aggregateCell = getCellContent([4, 0]);

    if (aggregateCell.kind === "number" && "data" in aggregateCell) {
      expect(aggregateCell.data).toBe(300);
    } else {
      throw new Error("Expected a number cell with data for aggregate column");
    }
  });

  test("correctly handles data columns when non-data columns are removed", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "data2",
        title: "TS 2",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "data3",
        title: "TS 3",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];

    const data = [
      [100, 200, 300],
      [150, 250, 350],
    ];

    const getCellContent = renderGridCellContent(data, columns);

    // Test all data columns
    for (let i = 0; i < 3; i++) {
      const cell = getCellContent([i, 0]);
      if (cell.kind === "number" && "data" in cell) {
        expect(cell.data).toBe(data[0][i]);
      } else {
        throw new Error(`Expected a number cell with data for column ${i}`);
      }
    }
  });
});

describe("useGridCellContent additional tests", () => {
  test("handles empty data array correctly", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];
    const data: number[][] = [];

    const getCellContent = renderGridCellContent(data, columns);

    const cell = getCellContent([0, 0]);
    if (cell.kind === "number" && "data" in cell) {
      expect(cell.data).toBeUndefined();
    } else {
      throw new Error("Expected a number cell with undefined data");
    }
  });

  test("handles column access out of bounds", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];
    const data = [[100]];

    const getCellContent = renderGridCellContent(data, columns);

    const cell = getCellContent([1, 0]); // Accessing column index 1 which doesn't exist
    expect(cell.kind).toBe("text");
    if ("displayData" in cell) {
      expect(cell.displayData).toBe("N/A");
    } else {
      throw new Error("Expected a text cell with 'N/A' displayData");
    }
  });

  test("handles row access out of bounds", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];
    const data = [[100]];

    const getCellContent = renderGridCellContent(data, columns);

    const cell = getCellContent([0, 1]); // Accessing row index 1 which doesn't exist
    if (cell.kind === "number" && "data" in cell) {
      expect(cell.data).toBeUndefined();
    } else {
      throw new Error("Expected a number cell with undefined data");
    }
  });

  test("handles missing aggregates correctly", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "total",
        title: "Total",
        type: ColumnTypes.Aggregate,
        width: 100,
        editable: false,
      },
    ];
    const data = [[100]];
    // No aggregates provided

    const getCellContent = renderGridCellContent(data, columns);

    const cell = getCellContent([0, 0]);
    if (cell.kind === "number" && "data" in cell) {
      expect(cell.data).toBeUndefined();
    } else {
      throw new Error(
        "Expected a number cell with undefined data for missing aggregate",
      );
    }
  });

  test("handles mixed editable and non-editable columns", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
      {
        id: "data2",
        title: "TS 2",
        type: ColumnTypes.Number,
        width: 50,
        editable: false,
      },
    ];
    const data = [[100, 200]];

    const getCellContent = renderGridCellContent(data, columns);

    const editableCell = getCellContent([0, 0]);
    const nonEditableCell = getCellContent([1, 0]);

    if (editableCell.kind === "number" && nonEditableCell.kind === "number") {
      expect(editableCell.readonly).toBe(false);
      expect(nonEditableCell.readonly).toBe(true);
    } else {
      throw new Error("Expected number cells with correct readonly property");
    }
  });

  test("handles very large numbers correctly", () => {
    const columns: EnhancedGridColumn[] = [
      {
        id: "data1",
        title: "TS 1",
        type: ColumnTypes.Number,
        width: 50,
        editable: true,
      },
    ];
    const largeNumber = 1e20;
    const data = [[largeNumber]];

    const getCellContent = renderGridCellContent(data, columns);

    const cell = getCellContent([0, 0]);
    if (cell.kind === "number" && "data" in cell) {
      expect(cell.data).toBe(largeNumber);
      expect(cell.displayData).toBe(largeNumber.toString());
    } else {
      throw new Error("Expected a number cell with correct large number data");
    }
  });
});
