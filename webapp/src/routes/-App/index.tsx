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

import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import HydroMatrix from "../_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/HydroMatrix";
import SplitHydroMatrix from "../_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/SplitHydroMatrix";
import { HYDRO_ROUTES } from "../_authenticated/studies/$studyId/explore/modeling/areas/$areaId/hydro/utils";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="area/:areaId">
          <Route path="hydro" element={<Navigate to="management" replace />} />
          <Route path="hydro">
            {HYDRO_ROUTES.map(({ path, type, isSplitView, splitConfig }) => {
              return isSplitView && splitConfig ? (
                <Route
                  key={path}
                  path={path}
                  element={
                    <SplitHydroMatrix
                      types={[type, splitConfig.partnerType]}
                      direction={splitConfig.direction}
                      sizes={splitConfig.sizes}
                    />
                  }
                />
              ) : (
                <Route key={path} path={path} element={<HydroMatrix type={type} />} />
              );
            })}
          </Route>
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
