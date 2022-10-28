import {
  BrowserRouter as Router,
  Navigate,
  Route,
  Routes,
  Outlet,
} from "react-router-dom";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { SnackbarProvider } from "notistack";
import maintheme from "../../theme";
import MenuWrapper from "../wrappers/MenuWrapper";
import Studies from "./Studies";
import Data from "./Data";
import Tasks from "./Tasks";
import Settings from "./Settings";
import Api from "./Api";
import LoginWrapper from "../wrappers/LoginWrapper";
import MaintenanceWrapper from "../wrappers/MaintenanceWrapper";
import SingleStudy from "./Singlestudy";
import Modelization from "./Singlestudy/explore/Modelization";
import Results from "./Singlestudy/explore/Results";
import Configuration from "./Singlestudy/explore/Configuration";
import BindingConstraints from "./Singlestudy/explore/Modelization/BindingConstraints";
import Links from "./Singlestudy/explore/Modelization/Links";
import Areas from "./Singlestudy/explore/Modelization/Areas";
import Map from "./Singlestudy/explore/Modelization/Map";
import DebugView from "./Singlestudy/explore/Modelization/DebugView";
import Xpansion from "./Singlestudy/explore/Xpansion";
import Candidates from "./Singlestudy/explore/Xpansion/Candidates";
import XpansionSettings from "./Singlestudy/explore/Xpansion/Settings";
import Capacities from "./Singlestudy/explore/Xpansion/Capacities";
import Properties from "./Singlestudy/explore/Modelization/Areas/Properties";
import Load from "./Singlestudy/explore/Modelization/Areas/Load";
import Thermal from "./Singlestudy/explore/Modelization/Areas/Thermal";
import Hydro from "./Singlestudy/explore/Modelization/Areas/Hydro";
import MiscGen from "./Singlestudy/explore/Modelization/Areas/MiscGen";
import Reserve from "./Singlestudy/explore/Modelization/Areas/Reserve";
import Wind from "./Singlestudy/explore/Modelization/Areas/Wind";
import Solar from "./Singlestudy/explore/Modelization/Areas/Solar";
import Renewables from "./Singlestudy/explore/Modelization/Areas/Renewables";
import ResultDetails from "./Singlestudy/explore/Results/ResultDetails";
import Constraints from "./Singlestudy/explore/Xpansion/Constraints";
import Weights from "./Singlestudy/explore/Xpansion/Weights";
import TableMode from "./Singlestudy/explore/Modelization/TableMode";
import TimeSeries from "./Singlestudy/explore/Modelization/Areas/Hydro/TimeSeries";
import HydroStorage from "./Singlestudy/explore/Modelization/Areas/Hydro/TimeSeries/HydroStorage";
import RunOfRiver from "./Singlestudy/explore/Modelization/Areas/Hydro/TimeSeries/RunOfRiver";
import Allocation from "./Singlestudy/explore/Modelization/Areas/Hydro/Allocation";
import ManagementOptions from "./Singlestudy/explore/Modelization/Areas/Hydro/ManagementOptions";
import DailyPower from "./Singlestudy/explore/Modelization/Areas/Hydro/DailyPower";
import ReservoirLevels from "./Singlestudy/explore/Modelization/Areas/Hydro/ReservoirLevels";
import WaterValues from "./Singlestudy/explore/Modelization/Areas/Hydro/WaterValues";
import EnergyCredits from "./Singlestudy/explore/Modelization/Areas/Hydro/EnergyCredits";

function App() {
  return (
    <Router>
      <ThemeProvider theme={maintheme}>
        <SnackbarProvider maxSnack={5}>
          <CssBaseline />
          <MaintenanceWrapper>
            <LoginWrapper>
              <MenuWrapper>
                <Routes>
                  <Route path="/studies" element={<Outlet />}>
                    <Route index element={<Studies />} />
                    <Route path=":studyId" element={<Outlet />}>
                      <Route index element={<SingleStudy />} />
                      <Route
                        path="explore"
                        element={<SingleStudy isExplorer />}
                      >
                        <Route path="modelization" element={<Modelization />}>
                          <Route path="map" element={<Map />} />
                          <Route path="area" element={<Areas />}>
                            <Route path="properties" element={<Properties />} />
                            <Route path="load" element={<Load />} />
                            <Route path="thermal" element={<Thermal />} />
                            <Route
                              path="hydro"
                              element={<Navigate to="management" replace />}
                            />
                            <Route path="hydro" element={<Hydro />}>
                              <Route
                                path="management"
                                element={<ManagementOptions />}
                              />
                              <Route
                                path="allocation"
                                element={<Allocation />}
                              />
                              <Route
                                path="dailypower"
                                element={<DailyPower />}
                              />
                              <Route
                                path="energycredits"
                                element={<EnergyCredits />}
                              />
                              <Route
                                path="reservoirlevels"
                                element={<ReservoirLevels />}
                              />
                              <Route
                                path="watervalues"
                                element={<WaterValues />}
                              />
                              <Route
                                path="timeseries"
                                element={<Navigate to="hydrostorage" replace />}
                              />
                              <Route path="timeseries" element={<TimeSeries />}>
                                <Route
                                  path="hydrostorage"
                                  element={<HydroStorage />}
                                />
                                <Route path="ror" element={<RunOfRiver />} />
                              </Route>
                            </Route>
                            <Route path="wind" element={<Wind />} />
                            <Route path="solar" element={<Solar />} />
                            <Route path="renewables" element={<Renewables />} />
                            <Route path="reserves" element={<Reserve />} />
                            <Route path="miscGen" element={<MiscGen />} />
                            <Route index element={<Properties />} />
                            <Route path="*" element={<Properties />} />
                          </Route>
                          <Route path="links" element={<Links />} />
                          <Route
                            path="bindingcontraint"
                            element={<BindingConstraints />}
                          />
                          <Route path="debug" element={<DebugView />} />
                          <Route path="tablemode" element={<TableMode />} />
                          <Route index element={<Map />} />
                          <Route path="*" element={<Map />} />
                        </Route>
                        <Route
                          path="configuration"
                          element={<Configuration />}
                        />
                        <Route path="xpansion" element={<Xpansion />}>
                          <Route path="candidates" element={<Candidates />} />
                          <Route
                            path="settings"
                            element={<XpansionSettings />}
                          />
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
              </MenuWrapper>
            </LoginWrapper>
          </MaintenanceWrapper>
        </SnackbarProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
