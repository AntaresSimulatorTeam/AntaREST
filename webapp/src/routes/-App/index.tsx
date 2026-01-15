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

// @ts-expect-error Temporary fix for missing lib
import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Solar from "../_authenticated/studies/$studyId/explore/modeling/areas/$areaId/Solar";
import Hydro from "./Singlestudy/explore/Modelization/Areas/Hydro";
import Allocation from "./Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import Correlation from "./Singlestudy/explore/Modelization/Areas/Hydro/Correlation";
import HydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/HydroMatrix";
import ManagementOptions from "./Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import SplitHydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/SplitHydroMatrix";
import { HYDRO_ROUTES } from "./Singlestudy/explore/Modelization/Areas/Hydro/utils";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="area/:areaId">
          <Route path="hydro" element={<Navigate to="management" replace />} />
          <Route path="hydro" element={<Hydro />}>
            <Route path="management" element={<ManagementOptions />} />
            <Route path="allocation" element={<Allocation />} />
            <Route path="correlation" element={<Correlation />} />
            {HYDRO_ROUTES.map(({ path, type, isSplitView, splitConfig, form, sx }) => {
              return isSplitView && splitConfig ? (
                <Route
                  key={path}
                  path={path}
                  element={
                    <SplitHydroMatrix
                      types={[type, splitConfig.partnerType]}
                      direction={splitConfig.direction}
                      sizes={splitConfig.sizes}
                      form={form}
                      sx={sx}
                    />
                  }
                />
              ) : (
                <Route key={path} path={path} element={<HydroMatrix type={type} />} />
              );
            })}
          </Route>

          <Route path="solar" element={<Solar />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
