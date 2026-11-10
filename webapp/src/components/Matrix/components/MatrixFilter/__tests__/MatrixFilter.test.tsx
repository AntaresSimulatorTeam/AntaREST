/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import matrixFilters, { setMatrixFilters } from "@/redux/ducks/matrixFilters";
import { UTCDate } from "@date-fns/utc";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode } from "react";
import { Provider } from "react-redux";
import MatrixFilter from "..";
import {
  MatrixProvider,
  useMatrixContext,
  type MatrixContextValue,
} from "../../../context/MatrixContext";
import { TimeFrequency } from "../../../shared/constants";
import type { DateTimes } from "../../../shared/types";
import { FILTER_OPERATORS, FILTER_TYPES, TIME_INDEXING } from "../constants";
import type { PersistedMatrixFilters } from "../types";

vi.mock("react-i18next", async (importOriginal) => ({
  ...(await importOriginal<typeof import("react-i18next")>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));

const PERSISTENCE = { studyId: "study", key: "load" };
const STORAGE_KEY = JSON.stringify([PERSISTENCE.key, TimeFrequency.Hourly]);

const SAVED_FILTERS: PersistedMatrixFilters = {
  active: true,
  columnsFilter: {
    type: FILTER_TYPES.LIST,
    list: [2, 4],
    operator: FILTER_OPERATORS.EQUALS,
  },
  rowsFilters: [
    {
      id: "hour-filter",
      indexingType: TIME_INDEXING.DAY_HOUR,
      type: FILTER_TYPES.LIST,
      list: [1, 3],
      operator: FILTER_OPERATORS.EQUALS,
    },
  ],
};

const AREA_DATA = [
  [10, 11, 12, 13],
  [20, 21, 22, 23],
  [30, 31, 32, 33],
  [40, 41, 42, 43],
];

const AREA_DATES: DateTimes = {
  values: [0, 1, 2, 3].map((hour) => new UTCDate(2026, 0, 1, hour)),
  first_week_size: 4,
  level: TimeFrequency.Hourly,
};

const EXPECTED_PREVIEW = {
  active: true,
  criteria: { columnsIndices: [1, 3], rowsIndices: [1, 3] },
};

function createTestStore() {
  const store = configureStore({ reducer: { matrixFilters } });
  store.dispatch(
    setMatrixFilters({
      studyId: PERSISTENCE.studyId,
      key: STORAGE_KEY,
      filters: SAVED_FILTERS,
    }),
  );
  return store;
}

function FilterPreview() {
  const { filterPreview } = useMatrixContext();
  return <output data-testid="filter-preview">{JSON.stringify(filterPreview)}</output>;
}

interface TestMatrixProps {
  store: ReturnType<typeof createTestStore>;
  areaId?: string;
  data?: number[][];
  dateTime?: DateTimes;
  readOnly?: boolean;
  setMatrixData?: MatrixContextValue["setMatrixData"];
}

function TestMatrix({
  store,
  areaId = "area-a",
  data = AREA_DATA,
  dateTime = AREA_DATES,
  readOnly = true,
  setMatrixData = vi.fn(),
}: TestMatrixProps) {
  return (
    <StrictMode>
      <Provider store={store}>
        <MatrixProvider
          key={areaId}
          currentState={{ data, aggregates: {} }}
          isSubmitting={false}
          updateCount={0}
          aggregateTypes={[]}
          setMatrixData={setMatrixData}
          undo={vi.fn()}
          redo={vi.fn()}
          canUndo={false}
          canRedo={false}
          isDirty={false}
        >
          <MatrixFilter
            dateTime={dateTime}
            isTimeSeries
            timeFrequency={TimeFrequency.Hourly}
            persistence={PERSISTENCE}
            readOnly={readOnly}
          />
          <FilterPreview />
        </MatrixProvider>
      </Provider>
    </StrictMode>
  );
}

test("restores the preview on mount and recomputes safe indices across area changes", () => {
  const store = createTestStore();
  const { rerender } = render(<TestMatrix store={store} />);

  expect(screen.getByTestId("filter-preview").textContent).toBe(JSON.stringify(EXPECTED_PREVIEW));

  const shorterData = [
    [50, 51],
    [60, 61],
    [70, 71],
  ];
  const shiftedDates: DateTimes = {
    ...AREA_DATES,
    values: [2, 3, 4].map((hour) => new UTCDate(2026, 0, 1, hour)),
  };

  rerender(<TestMatrix store={store} areaId="area-b" data={shorterData} dateTime={shiftedDates} />);

  expect(screen.getByTestId("filter-preview").textContent).toBe(
    JSON.stringify({
      active: true,
      criteria: { columnsIndices: [1], rowsIndices: [1] },
    }),
  );

  rerender(<TestMatrix store={store} />);

  expect(screen.getByTestId("filter-preview").textContent).toBe(JSON.stringify(EXPECTED_PREVIEW));
});

test("toggles restored filters and resets their saved configuration from the drawer", async () => {
  const user = userEvent.setup();
  const store = createTestStore();
  render(<TestMatrix store={store} />);
  const unfilteredPreview = {
    active: false,
    criteria: { columnsIndices: [0, 1, 2, 3], rowsIndices: [0, 1, 2, 3] },
  };

  await user.click(screen.getByRole("button", { name: "matrix.filter.filterData" }));
  await user.click(screen.getByRole("button", { name: "matrix.filter.active" }));

  expect(screen.getByTestId("filter-preview").textContent).toBe(JSON.stringify(unfilteredPreview));

  await user.click(screen.getByRole("button", { name: "matrix.filter.inactive" }));

  expect(screen.getByTestId("filter-preview").textContent).toBe(JSON.stringify(EXPECTED_PREVIEW));

  await user.click(screen.getByRole("button", { name: "matrix.filter.resetFilters" }));

  expect(screen.getByTestId("filter-preview").textContent).toBe(JSON.stringify(unfilteredPreview));
  expect(store.getState().matrixFilters[PERSISTENCE.studyId]?.[STORAGE_KEY]).toBeUndefined();
});

test("reset restores the displayed operand and an empty operand cannot apply a stale value", async () => {
  const user = userEvent.setup();
  const store = createTestStore();
  const setMatrixData = vi.fn();
  render(<TestMatrix store={store} readOnly={false} setMatrixData={setMatrixData} />);

  await user.click(screen.getByRole("button", { name: "matrix.filter.filterData" }));
  const operand = screen.getByRole("spinbutton", { name: "matrix.filter.value" });
  const apply = screen.getByRole("button", { name: "matrix.filter.applyOperation" });

  await user.clear(operand);
  await user.type(operand, "37");
  await user.click(apply);

  expect(setMatrixData).toHaveBeenLastCalledWith({
    data: [
      [10, 11, 12, 13],
      [20, 37, 22, 37],
      [30, 31, 32, 33],
      [40, 37, 42, 37],
    ],
    aggregates: {},
  });

  await user.clear(operand);

  expect(apply).toBeDisabled();

  await user.type(operand, "37");
  await user.click(screen.getByRole("button", { name: "matrix.filter.resetFilters" }));

  expect(operand).toHaveValue(0);
});

test("absolute value can apply without an operand", async () => {
  const user = userEvent.setup();
  const store = createTestStore();
  const setMatrixData = vi.fn();
  const data = AREA_DATA.map((row) => row.map((value) => -value));
  render(<TestMatrix store={store} data={data} readOnly={false} setMatrixData={setMatrixData} />);

  await user.click(screen.getByRole("button", { name: "matrix.filter.filterData" }));
  await user.clear(screen.getByRole("spinbutton", { name: "matrix.filter.value" }));
  await user.click(screen.getByText("matrix.operation.equal"));
  await user.click(screen.getByRole("option", { name: "matrix.operation.absolute" }));
  const apply = screen.getByRole("button", { name: "matrix.filter.applyOperation" });

  await user.click(apply);

  expect(setMatrixData).toHaveBeenCalledWith({
    data: [
      [-10, -11, -12, -13],
      [-20, 21, -22, 23],
      [-30, -31, -32, -33],
      [-40, 41, -42, 43],
    ],
    aggregates: {},
  });
});
