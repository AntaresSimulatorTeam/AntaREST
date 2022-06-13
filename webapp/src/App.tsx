import {
  BrowserRouter as Router,
  Navigate,
  Route,
  Routes,
  Outlet,
} from "react-router-dom";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { SnackbarProvider } from "notistack";
import maintheme from "./theme";
import MenuWrapper from "./pages/wrappers/MenuWrapper";
import Studies from "./pages/Studies";
import Data from "./pages/Data";
import Tasks from "./pages/Tasks";
import Settings from "./pages/Settings";
import Api from "./pages/Api";
import LoginWrapper from "./pages/wrappers/LoginWrapper";
import MaintenanceWrapper from "./pages/wrappers/MaintenanceWrapper";
import SingleStudy from "./pages/SingleStudy";
import Modelization from "./components/singlestudy/explore/Modelization";
import Results from "./components/singlestudy/explore/Results";
import Configuration from "./components/singlestudy/explore/Configuration";
import BindingConstraints from "./components/singlestudy/explore/Modelization/BindingConstraints";
import Links from "./components/singlestudy/explore/Modelization/Links";
import Areas from "./components/singlestudy/explore/Modelization/Areas";
import Map from "./components/singlestudy/explore/Modelization/Map";
import DebugView from "./components/singlestudy/explore/Modelization/DebugView";
import Xpansion from "./components/singlestudy/explore/Xpansion";
import Candidates from "./components/singlestudy/explore/Xpansion/Candidates";
import XpansionSettings from "./components/singlestudy/explore/Xpansion/Settings";
import Capacities from "./components/singlestudy/explore/Xpansion/Capacities";
import Files from "./components/singlestudy/explore/Xpansion/Files";
import Properties from "./components/singlestudy/explore/Modelization/Areas/Properties";
import Load from "./components/singlestudy/explore/Modelization/Areas/Load";
import Thermal from "./components/singlestudy/explore/Modelization/Areas/Thermal";
import Hydro from "./components/singlestudy/explore/Modelization/Areas/Hydro";
import MiscGen from "./components/singlestudy/explore/Modelization/Areas/MiscGen";
import Reserve from "./components/singlestudy/explore/Modelization/Areas/Reserve";
import Wind from "./components/singlestudy/explore/Modelization/Areas/Wind";
import Solar from "./components/singlestudy/explore/Modelization/Areas/Solar";
import Renewables from "./components/singlestudy/explore/Modelization/Areas/Renewables";

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
                            <Route path="hydro" element={<Hydro />} />
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
                          <Route path="files" element={<Files />} />
                          <Route path="capacities" element={<Capacities />} />
                          <Route index element={<Candidates />} />
                          <Route path="*" element={<Candidates />} />
                        </Route>
                        <Route path="results" element={<Results />} />
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
