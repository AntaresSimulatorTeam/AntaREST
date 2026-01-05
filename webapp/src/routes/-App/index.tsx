/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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
import Hydro from "./Singlestudy/explore/Modelization/Areas/Hydro";
import Allocation from "./Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import Correlation from "./Singlestudy/explore/Modelization/Areas/Hydro/Correlation";
import HydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/HydroMatrix";
import ManagementOptions from "./Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import SplitHydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/SplitHydroMatrix";
import { HYDRO_ROUTES } from "./Singlestudy/explore/Modelization/Areas/Hydro/utils";
import MiscGen from "./Singlestudy/explore/Modelization/Areas/MiscGen";
import Reserve from "./Singlestudy/explore/Modelization/Areas/Reserve";
import Solar from "./Singlestudy/explore/Modelization/Areas/Solar";
import Wind from "./Singlestudy/explore/Modelization/Areas/Wind";
import BindingConstraints from "./Singlestudy/explore/Modelization/BindingConstraints";
import Links from "./Singlestudy/explore/Modelization/Links";

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

          <Route path="wind" element={<Wind />} />

          <Route path="solar" element={<Solar />} />

          <Route path="reserves" element={<Reserve />} />

          <Route path="miscGen" element={<MiscGen />} />
        </Route>

        <Route path="links" element={<Links />} />

        <Route path="bindingcontraint" element={<BindingConstraints />} />
      </Routes>
    </Router>
  );
}

export default App;
