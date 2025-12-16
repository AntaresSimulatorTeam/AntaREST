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

import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Areas from "../_authenticated/studies/$studyId/explore/modelization/areas";
import Hydro from "./Singlestudy/explore/Modelization/Areas/Hydro";
import Allocation from "./Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import Correlation from "./Singlestudy/explore/Modelization/Areas/Hydro/Correlation";
import HydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/HydroMatrix";
import ManagementOptions from "./Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import SplitHydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/SplitHydroMatrix";
import { HYDRO_ROUTES } from "./Singlestudy/explore/Modelization/Areas/Hydro/utils";
import Load from "./Singlestudy/explore/Modelization/Areas/Load";
import MiscGen from "./Singlestudy/explore/Modelization/Areas/MiscGen";
import Properties from "./Singlestudy/explore/Modelization/Areas/Properties";
import Renewables from "./Singlestudy/explore/Modelization/Areas/Renewables";
import RenewableConfig from "./Singlestudy/explore/Modelization/Areas/Renewables/RenewableConfig";
import Reserve from "./Singlestudy/explore/Modelization/Areas/Reserve";
import Solar from "./Singlestudy/explore/Modelization/Areas/Solar";
import Storages from "./Singlestudy/explore/Modelization/Areas/Storages";
import StorageConfig from "./Singlestudy/explore/Modelization/Areas/Storages/StorageConfig";
import Thermal from "./Singlestudy/explore/Modelization/Areas/Thermal";
import ThermalConfig from "./Singlestudy/explore/Modelization/Areas/Thermal/ThermalConfig";
import Wind from "./Singlestudy/explore/Modelization/Areas/Wind";
import BindingConstraints from "./Singlestudy/explore/Modelization/BindingConstraints";
import Links from "./Singlestudy/explore/Modelization/Links";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="area" element={<Areas />} />
        <Route path="area/:areaId" element={<Areas />}>
          <Route path="properties" element={<Properties />} />
          <Route path="load" element={<Load />} />
          <Route path="thermal" element={<Thermal />} />
          <Route path="thermal/:clusterId" element={<ThermalConfig />} />
          <Route path="storages" element={<Storages />} />
          <Route path="storages/:storageId" element={<StorageConfig />} />
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
          <Route path="renewables" element={<Renewables />} />
          <Route path="renewables/:clusterId" element={<RenewableConfig />} />
          <Route path="reserves" element={<Reserve />} />
          <Route path="miscGen" element={<MiscGen />} />
          <Route index element={<Properties />} />
          <Route path="*" element={<Properties />} />
        </Route>
        <Route path="links" element={<Links />} />
        <Route path="bindingcontraint" element={<BindingConstraints />} />
      </Routes>
    </Router>
  );
}

export default App;
