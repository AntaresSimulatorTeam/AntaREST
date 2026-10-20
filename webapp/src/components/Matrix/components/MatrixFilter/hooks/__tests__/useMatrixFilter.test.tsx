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

import { MatrixContext, type MatrixContextValue } from "@/components/Matrix/context/MatrixContext";
import { Operation, TimeFrequency } from "@/components/Matrix/shared/constants";
import matrixFilters from "@/redux/ducks/matrixFilters";
import { configureStore } from "@reduxjs/toolkit";
import { act, renderHook } from "@testing-library/react";
import { StrictMode } from "react";
import { Provider } from "react-redux";
import { FILTER_TYPES, TIME_INDEXING } from "../../constants";
import { useFilteredData } from "../useFilteredData";
import { useMatrixFilter } from "../useMatrixFilter";

const context: MatrixContextValue = {
  currentState: {
    data: [
      [1, 2],
      [3, 4],
    ],
    aggregates: {},
  },
  isSubmitting: false,
  updateCount: 0,
  aggregateTypes: [],
  setMatrixData: vi.fn(),
  undo: vi.fn(),
  redo: vi.fn(),
  canUndo: false,
  canRedo: false,
  isDirty: false,
  filterPreview: { active: false, criteria: { rowsIndices: [], columnsIndices: [] } },
  setFilterPreview: vi.fn(),
};

const createStore = () => configureStore({ reducer: { matrixFilters } });
type FilterParams = Parameters<typeof useMatrixFilter>[0];

function renderFilters(
  store: ReturnType<typeof createStore>,
  overrides: Partial<FilterParams> = {},
) {
  const initialProps: FilterParams = {
    rowCount: 4,
    columnCount: 5,
    timeFrequency: TimeFrequency.Hourly,
    persistence: { studyId: "study-a", key: "load" },
    ...overrides,
  };

  return renderHook(
    (props: FilterParams) => {
      const controls = useMatrixFilter(props);
      const criteria = useFilteredData({ ...props, filter: controls.filter, isTimeSeries: false });
      return { ...controls, criteria };
    },
    {
      initialProps,
      wrapper: ({ children }) => (
        <StrictMode>
          <Provider store={store}>
            <MatrixContext.Provider value={context}>{children}</MatrixContext.Provider>
          </Provider>
        </StrictMode>
      ),
    },
  );
}

function configureFilters({ result }: ReturnType<typeof renderFilters>) {
  act(() => {
    result.current.setFilter((previous) => ({
      ...previous,
      active: true,
      columnsFilter: { type: FILTER_TYPES.RANGE, range: { min: 3, max: 5 } },
      rowsFilters: [
        {
          id: "row-filter",
          type: FILTER_TYPES.RANGE,
          indexingType: TIME_INDEXING.HOUR_YEAR,
          range: { min: 2, max: 4 },
        },
      ],
    }));
  });
}

test("remembers each view, study and frequency independently", () => {
  const store = createStore();
  const load = renderFilters(store);
  configureFilters(load);
  load.unmount();

  const wind = renderFilters(store, { persistence: { studyId: "study-a", key: "wind" } });
  expect(wind.result.current.filter.active).toBe(false);
  act(() =>
    wind.result.current.setFilter((previous) => ({
      ...previous,
      active: true,
      columnsFilter: { type: FILTER_TYPES.LIST, list: [1] },
    })),
  );
  wind.unmount();

  for (const overrides of [
    { persistence: { studyId: "study-b", key: "load" } },
    { timeFrequency: TimeFrequency.Daily },
  ]) {
    const other = renderFilters(store, overrides);
    expect(other.result.current.filter.active).toBe(false);
    other.unmount();
  }

  const returnedLoad = renderFilters(store);
  expect(returnedLoad.result.current.criteria.columnsIndices).toEqual([2, 3, 4]);
  returnedLoad.unmount();
  const returnedWind = renderFilters(store, { persistence: { studyId: "study-a", key: "wind" } });
  expect(returnedWind.result.current.criteria.columnsIndices).toEqual([0]);
});

test("retains disabled settings across remounts and reapplies them when enabled", () => {
  const store = createStore();
  const load = renderFilters(store);
  configureFilters(load);
  act(() => load.result.current.toggleFilter());
  load.unmount();

  const returned = renderFilters(store);
  expect(returned.result.current.filter.active).toBe(false);
  expect(returned.result.current.filter.columnsFilter.range).toEqual({ min: 3, max: 5 });
  act(() => returned.result.current.toggleFilter());
  expect(returned.result.current.criteria.columnsIndices).toEqual([2, 3, 4]);
});

test("composes batched updates while keeping operation controls out of Redux", () => {
  const store = createStore();
  const current = renderFilters(store);

  act(() => {
    current.result.current.setOperation((previous) => ({ ...previous, type: Operation.Add }));
    current.result.current.setOperation((previous) => ({ ...previous, value: 10 }));
    current.result.current.setFilter((previous) => ({ ...previous, active: true }));
    current.result.current.setFilter((previous) => ({
      ...previous,
      columnsFilter: { type: FILTER_TYPES.LIST, list: [2] },
    }));
  });

  expect(current.result.current.filter.operation).toEqual({ type: Operation.Add, value: 10 });
  expect(current.result.current.filter.active).toBe(true);
  expect(current.result.current.criteria.columnsIndices).toEqual([1]);
  const saved = Object.values(store.getState().matrixFilters["study-a"])[0];
  expect(saved).not.toHaveProperty("operation");
  expect(context.setMatrixData).not.toHaveBeenCalled();

  current.unmount();

  const nextArea = renderFilters(store);
  expect(nextArea.result.current.filter.operation).toEqual({ type: Operation.Eq, value: 0 });
  expect(nextArea.result.current.criteria.columnsIndices).toEqual([1]);
});

test("keeps criteria through no matches and empty data, then reapplies them", () => {
  const store = createStore();
  const current = renderFilters(store);
  configureFilters(current);

  for (const dimensions of [
    { rowCount: 1, columnCount: 2 },
    { rowCount: 0, columnCount: 0 },
  ]) {
    current.rerender({
      ...dimensions,
      timeFrequency: TimeFrequency.Hourly,
      persistence: { studyId: "study-a", key: "load" },
    });

    expect(current.result.current.criteria).toEqual({ rowsIndices: [], columnsIndices: [] });
  }

  current.rerender({
    rowCount: 4,
    columnCount: 5,
    timeFrequency: TimeFrequency.Hourly,
    persistence: { studyId: "study-a", key: "load" },
  });

  expect(current.result.current.criteria).toEqual({
    rowsIndices: [1, 2, 3],
    columnsIndices: [2, 3, 4],
  });
});

test("unconfigured matrices keep filters local", () => {
  const store = createStore();
  const local = renderFilters(store, { persistence: undefined });
  configureFilters(local);
  expect(local.result.current.filter.active).toBe(true);
  expect(store.getState().matrixFilters).toEqual({});
  local.unmount();
  const reopened = renderFilters(store, { persistence: undefined });
  expect(reopened.result.current.filter.active).toBe(false);
});
