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

import { AsyncThunk } from "@reduxjs/toolkit";
import { useEffect } from "react";
import { AppState } from "../ducks";
import { AppAsyncThunkConfig } from "../store";
import { AsyncEntityState, FetchStatus } from "../utils";
import useAppDispatch from "./useAppDispatch";
import useAppSelector from "./useAppSelector";

interface UseAsyncEntityStateParams<Entity, Selected> {
  entityStateSelector: (state: AppState) => AsyncEntityState<Entity>;
  fetchAction: AsyncThunk<Entity[], undefined, AppAsyncThunkConfig>;
  valueSelector: (state: AppState) => Selected;
}

export interface UseAsyncEntityStateResponse<Entity, Selected>
  extends Pick<AsyncEntityState<Entity>, "status" | "error"> {
  value: Selected;
}

function useAsyncAppSelector<Entity, Selected>(
  params: UseAsyncEntityStateParams<Entity, Selected>,
): UseAsyncEntityStateResponse<Entity, Selected> {
  const { entityStateSelector, fetchAction, valueSelector } = params;
  const status = useAppSelector((state) => entityStateSelector(state).status);
  const error = useAppSelector((state) => entityStateSelector(state).error);
  const value = useAppSelector(valueSelector);
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (status === FetchStatus.Idle) {
      dispatch(fetchAction());
    }
  }, [dispatch, fetchAction, status]);

  return { status, error, value };
}

export default useAsyncAppSelector;
