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
import { createAction, createReducer } from "@reduxjs/toolkit";
import type { AppState } from ".";
import { makeActionName } from "../utils";

interface MatrixFiltersKey {
  studyId: string;
  key: string;
}

type MatrixFiltersState = Record<string, Record<string, PersistedMatrixFilters>>;

const initialState: MatrixFiltersState = {};
const n = makeActionName("matrixFilters");

export const setMatrixFilters = createAction<
  MatrixFiltersKey & { filters: PersistedMatrixFilters }
>(n("SET_MATRIX_FILTERS"));

export const resetMatrixFilters = createAction<MatrixFiltersKey>(n("RESET_MATRIX_FILTERS"));

export const getMatrixFilters = (
  { matrixFilters }: Pick<AppState, "matrixFilters">,
  { studyId, key }: MatrixFiltersKey,
): PersistedMatrixFilters | undefined => matrixFilters[studyId]?.[key];

export default createReducer(initialState, (builder) => {
  builder
    .addCase(setMatrixFilters, (draftState, { payload: { studyId, key, filters } }) => {
      draftState[studyId] ??= {};
      draftState[studyId][key] = filters;
    })
    .addCase(resetMatrixFilters, (draftState, { payload: { studyId, key } }) => {
      delete draftState[studyId]?.[key];
    });
});
