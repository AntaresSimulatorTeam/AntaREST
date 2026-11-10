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

import type { PersistedMatrixFilters } from "@/components/Matrix/components/MatrixFilter/types";
import { configureStore } from "@reduxjs/toolkit";
import rootReducer from "..";
import { logout } from "../auth";
import matrixFilters, {
  getMatrixFilters,
  resetMatrixFilters,
  setMatrixFilters,
} from "../matrixFilters";

vi.mock("@/redux/store", () => ({ default: { dispatch: vi.fn() } }));

const loadFilters: PersistedMatrixFilters = {
  active: true,
  columnsFilter: { type: "range", range: { min: 2, max: 5 } },
  rowsFilters: [{ id: "month", indexingType: "month", type: "list", list: [1] }],
};

const windFilters: PersistedMatrixFilters = {
  active: false,
  columnsFilter: { type: "list", list: [3] },
  rowsFilters: [{ id: "hour", indexingType: "dayHour", type: "list", list: [12] }],
};

function createStore() {
  return configureStore({ reducer: { matrixFilters } });
}

test("resetting one view preserves the other views and studies", () => {
  const store = createStore();

  store.dispatch(setMatrixFilters({ studyId: "study-a", key: "load", filters: loadFilters }));
  store.dispatch(setMatrixFilters({ studyId: "study-a", key: "wind", filters: windFilters }));
  store.dispatch(setMatrixFilters({ studyId: "study-b", key: "load", filters: loadFilters }));

  store.dispatch(resetMatrixFilters({ studyId: "study-a", key: "load" }));

  expect(getMatrixFilters(store.getState(), { studyId: "study-a", key: "load" })).toBeUndefined();
  expect(getMatrixFilters(store.getState(), { studyId: "study-a", key: "wind" })).toEqual(
    windFilters,
  );
  expect(getMatrixFilters(store.getState(), { studyId: "study-b", key: "load" })).toEqual(
    loadFilters,
  );
});

test("logout clears all remembered matrix filters through the root reducer", () => {
  const store = configureStore({ reducer: rootReducer });

  store.dispatch(setMatrixFilters({ studyId: "study-a", key: "load", filters: loadFilters }));
  store.dispatch(setMatrixFilters({ studyId: "study-b", key: "wind", filters: windFilters }));

  store.dispatch({ type: logout.toString() });

  expect(store.getState().matrixFilters).toEqual({});
});
