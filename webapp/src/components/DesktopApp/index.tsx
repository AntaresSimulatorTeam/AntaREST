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
import CloseIcon from "@mui/icons-material/Close";
import { IconButton } from "@mui/material";
import { SnackbarProvider, useSnackbar, type SnackbarKey } from "notistack";
import { Provider } from "react-redux";
import { Navigate, Outlet, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import Api from "./../App/Api";
import Data from "./../App/Data";
import Login from "./../App/Login";
import Settings from "./../App/Settings";
import SingleStudy from "./../App/Singlestudy";
import Configuration from "./../App/Singlestudy/explore/Configuration";
import Debug from "./../App/Singlestudy/explore/Debug";
import Modelization from "./../App/Singlestudy/explore/Modelization";
import Areas from "./../App/Singlestudy/explore/Modelization/Areas";
import Hydro from "./../App/Singlestudy/explore/Modelization/Areas/Hydro";
import Allocation from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import Correlation from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/Correlation";
import HydroMatrix from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/HydroMatrix";
import ManagementOptions from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import SplitHydroMatrix from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/SplitHydroMatrix";
import { HYDRO_ROUTES } from "./../App/Singlestudy/explore/Modelization/Areas/Hydro/utils";
import Load from "./../App/Singlestudy/explore/Modelization/Areas/Load";
import MiscGen from "./../App/Singlestudy/explore/Modelization/Areas/MiscGen";
import Properties from "./../App/Singlestudy/explore/Modelization/Areas/Properties";
import Renewables from "./../App/Singlestudy/explore/Modelization/Areas/Renewables";
import RenewableConfig from "./../App/Singlestudy/explore/Modelization/Areas/Renewables/RenewableConfig";
import Reserve from "./../App/Singlestudy/explore/Modelization/Areas/Reserve";
import Solar from "./../App/Singlestudy/explore/Modelization/Areas/Solar";
import Storages from "./../App/Singlestudy/explore/Modelization/Areas/Storages";
import StorageForm from "./../App/Singlestudy/explore/Modelization/Areas/Storages/StorageConfig";
import Thermal from "./../App/Singlestudy/explore/Modelization/Areas/Thermal";
import ThermalConfig from "./../App/Singlestudy/explore/Modelization/Areas/Thermal/ThermalConfig";
import Wind from "./../App/Singlestudy/explore/Modelization/Areas/Wind";
import BindingConstraints from "./../App/Singlestudy/explore/Modelization/BindingConstraints";
import Links from "./../App/Singlestudy/explore/Modelization/Links";
import Map from "./../App/Singlestudy/explore/Modelization/Map";
import Districts from "./../App/Singlestudy/explore/Modelization/Map/MapConfig/Districts";
import Layers from "./../App/Singlestudy/explore/Modelization/Map/MapConfig/Layers";
import Results from "./../App/Singlestudy/explore/Results";
import ResultDetails from "./../App/Singlestudy/explore/Results/ResultDetails";
import TableModeList from "./../App/Singlestudy/explore/TableModeList";
import Xpansion from "./../App/Singlestudy/explore/Xpansion";
import Candidates from "./../App/Singlestudy/explore/Xpansion/Candidates";
import Capacities from "./../App/Singlestudy/explore/Xpansion/Capacities";
import Constraints from "./../App/Singlestudy/explore/Xpansion/Constraints";
import XpansionSettings from "./../App/Singlestudy/explore/Xpansion/Settings";
import Weights from "./../App/Singlestudy/explore/Xpansion/Weights";
import Studies from "./../App/Studies";
import Tasks from "./../App/Tasks";
import ThemeProvider from "./../App/ThemeProvider";
import { useNavigate } from "react-router";
import { useEffect } from "react";
import client from "@/services/api/client";
import SingleStudyPlaceholder from "@/components/DesktopApp/SingleStudyPlaceholder";

// TODO: replace 'notistack' by 'sonner' (https://sonner.emilkowal.ski/)
function SnackbarCloseButton({ snackbarKey }: { snackbarKey: SnackbarKey }) {
  const { closeSnackbar } = useSnackbar();

  return (
    <IconButton onClick={() => closeSnackbar(snackbarKey)}>
      <CloseIcon />
    </IconButton>
  );
}

function DesktopApp() {
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
            <Login>
              <Routes>
                <Route path="/studies" element={<Outlet />}>
                  <Route index element={<SingleStudyPlaceholder />} />
                  <Route path=":studyId" element={<Outlet />}>
                    <Route index element={<SingleStudy />} />
                    <Route path="explore" element={<SingleStudy isExplorer />}>
                      <Route path="modelization" element={<Modelization />}>
                        <Route path="map" element={<Map />}>
                          <Route path="layers" element={<Layers />} />
                          <Route path="districts" element={<Districts />} />
                        </Route>
                        <Route path="area" element={<Areas />} />
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
                              ({ path, type, isSplitView, splitConfig, form, sx }) => {
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
            </Login>
          </Router>
        </SnackbarProvider>
      </ThemeProvider>
    </Provider>
  );
}

export default DesktopApp;
