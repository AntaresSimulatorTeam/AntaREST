import { TimeMetadataDTO } from "./types";
import {
  ColumnDataType,
  generateDateTime,
  generateTimeSeriesColumns,
} from "./utils";

describe("generateDateTime", () => {
  test("generates correct number of dates", () => {
    const metadata: TimeMetadataDTO = {
      start_date: "2023-01-01T00:00:00Z",
      steps: 5,
      first_week_size: 7,
      level: "daily",
    };
    const result = generateDateTime(metadata);
    expect(result).toHaveLength(5);
  });

  test.each([
    {
      level: "hourly",
      start: "2023-01-01T00:00:00Z",
      expected: [
        "2023-01-01T00:00:00.000Z",
        "2023-01-01T01:00:00.000Z",
        "2023-01-01T02:00:00.000Z",
      ],
    },
    {
      level: "daily",
      start: "2023-01-01T00:00:00Z",
      expected: [
        "2023-01-01T00:00:00.000Z",
        "2023-01-02T00:00:00.000Z",
        "2023-01-03T00:00:00.000Z",
      ],
    },
    {
      level: "weekly",
      start: "2023-01-01T00:00:00Z",
      expected: [
        "2023-01-01T00:00:00.000Z",
        "2023-01-08T00:00:00.000Z",
        "2023-01-15T00:00:00.000Z",
      ],
    },
    {
      level: "monthly",
      start: "2023-01-15T00:00:00Z",
      expected: [
        "2023-01-15T00:00:00.000Z",
        "2023-02-15T00:00:00.000Z",
        "2023-03-15T00:00:00.000Z",
      ],
    },
    {
      level: "yearly",
      start: "2020-02-29T00:00:00Z",
      expected: ["2020-02-29T00:00:00.000Z", "2021-02-28T00:00:00.000Z"],
    },
  ] as const)(
    "generates correct dates for $level level",
    ({ level, start, expected }) => {
      const metadata: TimeMetadataDTO = {
        start_date: start,
        steps: expected.length,
        first_week_size: 7,
        level: level as TimeMetadataDTO["level"],
      };

      const result = generateDateTime(metadata);

      expect(result).toEqual(expected);
    },
  );

  test("handles edge cases", () => {
    const metadata: TimeMetadataDTO = {
      start_date: "2023-12-31T23:59:59Z",
      steps: 2,
      first_week_size: 7,
      level: "hourly",
    };
    const result = generateDateTime(metadata);
    expect(result).toEqual([
      "2023-12-31T23:59:59.000Z",
      "2024-01-01T00:59:59.000Z",
    ]);
  });
});

describe("generateTimeSeriesColumns", () => {
  test("generates correct number of columns", () => {
    const result = generateTimeSeriesColumns({ count: 5 });
    expect(result).toHaveLength(5);
  });

  test("generates columns with default options", () => {
    const result = generateTimeSeriesColumns({ count: 3 });
    expect(result).toEqual([
      {
        id: "data1",
        title: "TS 1",
        type: ColumnDataType.Number,
        style: "normal",
        width: 50,
        editable: true,
      },
      {
        id: "data2",
        title: "TS 2",
        type: ColumnDataType.Number,
        style: "normal",
        width: 50,
        editable: true,
      },
      {
        id: "data3",
        title: "TS 3",
        type: ColumnDataType.Number,
        style: "normal",
        width: 50,
        editable: true,
      },
    ]);
  });

  test("generates columns with custom options", () => {
    const result = generateTimeSeriesColumns({
      count: 2,
      startIndex: 10,
      prefix: "Data",
      width: 80,
      editable: false,
    });
    expect(result).toEqual([
      {
        id: "data10",
        title: "Data 10",
        type: ColumnDataType.Number,
        style: "normal",
        width: 80,
        editable: false,
      },
      {
        id: "data11",
        title: "Data 11",
        type: ColumnDataType.Number,
        style: "normal",
        width: 80,
        editable: false,
      },
    ]);
  });

  test("handles zero count", () => {
    const result = generateTimeSeriesColumns({ count: 0 });
    expect(result).toEqual([]);
  });

  test("handles large count", () => {
    const result = generateTimeSeriesColumns({ count: 1000 });
    expect(result).toHaveLength(1000);
    expect(result[999].id).toBe("data1000");
    expect(result[999].title).toBe("TS 1000");
  });

  test("maintains consistent type and style", () => {
    const result = generateTimeSeriesColumns({ count: 1000 });
    result.forEach((column) => {
      expect(column.type).toBe(ColumnDataType.Number);
      expect(column.style).toBe("normal");
    });
  });
});
