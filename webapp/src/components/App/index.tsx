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

import store from "@/redux/store";
import { Provider } from "react-redux";
import { BrowserRouter as Router, Navigate, Route, Routes, Outlet } from "react-router-dom";
import { IconButton } from "@mui/material";
import { SnackbarProvider, useSnackbar, type SnackbarKey } from "notistack";
import Studies from "./Studies";
import Data from "./Data";
import Tasks from "./Tasks";
import Settings from "./Settings";
import Api from "./Api";
import SingleStudy from "./Singlestudy";
import Modelization from "./Singlestudy/explore/Modelization";
import Results from "./Singlestudy/explore/Results";
import Configuration from "./Singlestudy/explore/Configuration";
import BindingConstraints from "./Singlestudy/explore/Modelization/BindingConstraints";
import Links from "./Singlestudy/explore/Modelization/Links";
import Areas from "./Singlestudy/explore/Modelization/Areas";
import Map from "./Singlestudy/explore/Modelization/Map";
import Debug from "./Singlestudy/explore/Debug";
import Xpansion from "./Singlestudy/explore/Xpansion";
import Candidates from "./Singlestudy/explore/Xpansion/Candidates";
import XpansionSettings from "./Singlestudy/explore/Xpansion/Settings";
import Capacities from "./Singlestudy/explore/Xpansion/Capacities";
import Properties from "./Singlestudy/explore/Modelization/Areas/Properties";
import Load from "./Singlestudy/explore/Modelization/Areas/Load";
import Hydro from "./Singlestudy/explore/Modelization/Areas/Hydro";
import MiscGen from "./Singlestudy/explore/Modelization/Areas/MiscGen";
import Reserve from "./Singlestudy/explore/Modelization/Areas/Reserve";
import Wind from "./Singlestudy/explore/Modelization/Areas/Wind";
import Solar from "./Singlestudy/explore/Modelization/Areas/Solar";
import ResultDetails from "./Singlestudy/explore/Results/ResultDetails";
import Constraints from "./Singlestudy/explore/Xpansion/Constraints";
import Weights from "./Singlestudy/explore/Xpansion/Weights";
import TableModeList from "./Singlestudy/explore/TableModeList";
import ManagementOptions from "./Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import { HYDRO_ROUTES } from "./Singlestudy/explore/Modelization/Areas/Hydro/utils";
import HydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/HydroMatrix";
import Layers from "./Singlestudy/explore/Modelization/Map/MapConfig/Layers";
import Districts from "./Singlestudy/explore/Modelization/Map/MapConfig/Districts";
import Allocation from "./Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import Correlation from "./Singlestudy/explore/Modelization/Areas/Hydro/Correlation";
import Storages from "./Singlestudy/explore/Modelization/Areas/Storages";
import StorageForm from "./Singlestudy/explore/Modelization/Areas/Storages/StorageConfig";
import Thermal from "./Singlestudy/explore/Modelization/Areas/Thermal";
import ThermalConfig from "./Singlestudy/explore/Modelization/Areas/Thermal/ThermalConfig";
import Renewables from "./Singlestudy/explore/Modelization/Areas/Renewables";
import RenewableConfig from "./Singlestudy/explore/Modelization/Areas/Renewables/RenewableConfig";
import SplitHydroMatrix from "./Singlestudy/explore/Modelization/Areas/Hydro/SplitHydroMatrix";
import CloseIcon from "@mui/icons-material/Close";
import ThemeProvider from "./ThemeProvider";
import MaintenanceMode from "./MaintenanceMode";
import Login from "./Login";
import Container from "./Container";

// TODO: replace 'notistack' by 'sonner' (https://sonner.emilkowal.ski/)
function SnackbarCloseButton({ snackbarKey }: { snackbarKey: SnackbarKey }) {
  const { closeSnackbar } = useSnackbar();

  return (
    <IconButton onClick={() => closeSnackbar(snackbarKey)}>
      <CloseIcon />
    </IconButton>
  );
}

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider>
        <SnackbarProvider
          maxSnack={5}
          autoHideDuration={3000}
          action={(key) => <SnackbarCloseButton snackbarKey={key} />}
          preventDuplicate
        >
          <Router>
            <MaintenanceMode>
              <Login>
                <Container>
                  <Routes>
                    <Route path="/studies" element={<Outlet />}>
                      <Route index element={<Studies />} />
                      <Route path=":studyId" element={<Outlet />}>
                        <Route index element={<SingleStudy />} />
                        <Route path="explore" element={<SingleStudy isExplorer />}>
                          <Route path="modelization" element={<Modelization />}>
                            <Route path="map" element={<Map />}>
                              <Route path="layers" element={<Layers />} />
                              <Route path="districts" element={<Districts />} />
                            </Route>
                            <Route path="area/:areaId" element={<Areas />}>
                              <Route path="properties" element={<Properties />} />
                              <Route path="load" element={<Load />} />
                              <Route path="thermal" element={<Thermal />} />
                              <Route path="thermal/:clusterId" element={<ThermalConfig />} />
                              <Route path="storages" element={<Storages />} />
                              <Route path="storages/:storageId" element={<StorageForm />} />
                              <Route path="hydro" element={<Navigate to="management" replace />} />
                              <Route path="hydro" element={<Hydro />}>
                                <Route path="management" element={<ManagementOptions />} />
                                <Route path="allocation" element={<Allocation />} />
                                <Route path="correlation" element={<Correlation />} />
                                {HYDRO_ROUTES.map(
                                  ({ path, type, isSplitView, splitConfig, form }) => {
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
                                          />
                                        }
                                      />
                                    ) : (
                                      <Route
                                        key={path}
                                        path={path}
                                        element={<HydroMatrix type={type} />}
                                      />
                                    );
                                  },
                                )}
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
                            <Route index element={<Map />} />
                            <Route path="*" element={<Map />} />
                          </Route>
                          <Route path="configuration" element={<Configuration />} />
                          <Route path="tablemode" element={<TableModeList />} />
                          <Route path="xpansion" element={<Xpansion />}>
                            <Route path="candidates" element={<Candidates />} />
                            <Route path="settings" element={<XpansionSettings />} />
                            <Route path="constraints" element={<Constraints />} />
                            <Route path="weights" element={<Weights />} />
                            <Route path="capacities" element={<Capacities />} />
                            <Route index element={<Candidates />} />
                            <Route path="*" element={<Candidates />} />
                          </Route>
                          <Route path="results">
                            <Route path=":outputId" element={<ResultDetails />} />
                            <Route index element={<Results />} />
                          </Route>
                          <Route path="debug" element={<Debug />} />
                          <Route path="*" element={<Modelization />}>
                            <Route index element={<Map />} />
                          </Route>
                        </Route>
                      </Route>
                    </Route>
                    <Route path="/data" element={<Data />} />
                    <Route path="/tasks" element={<Tasks />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/apidoc" element={<Api />} />
                    <Route path="*" element={<Navigate to="/studies" />} />
                  </Routes>
                </Container>
              </Login>
            </MaintenanceMode>
          </Router>
        </SnackbarProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
