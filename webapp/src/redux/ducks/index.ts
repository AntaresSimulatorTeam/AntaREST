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

import { Action, combineReducers } from "redux";
import { L } from "ts-toolbelt";
import studies from "./studies";
import users from "./users";
import groups from "./groups";
import auth, { logout } from "./auth";
import ui from "./ui";
import studySyntheses from "./studySyntheses";
import studyMaps from "./studyMaps";

const appReducer = combineReducers({
  studies,
  users,
  groups,
  auth,
  ui,
  studySyntheses,
  studyMaps,
});

type AppReducerType = typeof appReducer;
type AppReducerStateArg = L.Head<Parameters<AppReducerType>>;

export type AppState = ReturnType<AppReducerType>;

const rootReducer = (state: AppReducerStateArg, action: Action): AppState => {
  if (action.type === logout.toString()) {
    return appReducer(undefined, action);
  }
  return appReducer(state, action);
};

export default rootReducer;
