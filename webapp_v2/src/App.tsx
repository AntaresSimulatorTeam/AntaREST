/* eslint-disable react/no-unstable-nested-components */
/* eslint-disable react/jsx-props-no-spreading */
import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes, Outlet } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { SnackbarProvider } from 'notistack';
import maintheme from './theme';
import MenuWrapper from './pages/wrappers/MenuWrapper';
import Studies from './pages/Studies';
import Data from './pages/Data';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Api from './pages/Api';
import LoginWrapper from './pages/wrappers/LoginWrapper';
import MaintenanceWrapper from './pages/wrappers/MaintenanceWrapper';
import SingleStudy from './pages/SingleStudy';
import Modelization from './components/singlestudy/explore/Modelization';
import Results from './components/singlestudy/explore/Results';
import Configuration from './components/singlestudy/explore/Configuration';
import BindingContraint from './components/singlestudy/explore/Modelization/BindingContraint';
import Links from './components/singlestudy/explore/Modelization/Links';
import Area from './components/singlestudy/explore/Modelization/Area';
import Map from './components/singlestudy/explore/Modelization/Map';

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
                      <Route path="explore" element={<SingleStudy isExplorer />}>
                        <Route path="modelization" element={<Modelization />}>
                          <Route path="map" element={<Map />} />
                          <Route path="area" element={<Area />} />
                          <Route path="links" element={<Links />} />
                          <Route path="bindingcontraint" element={<BindingContraint />} />
                          <Route
                            index
                            element={<Map />}
                          />
                          <Route
                            path="*"
                            element={<Map />}
                          />
                        </Route>
                        <Route path="configuration" element={<Configuration />} />
                        <Route path="results" element={<Results />} />
                        <Route
                          path="*"
                          element={<Modelization />}
                        >
                          <Route
                            index
                            element={<Map />}
                          />
                        </Route>
                      </Route>
                    </Route>
                  </Route>
                  <Route path="/data" element={<Data />} />
                  <Route path="/tasks" element={<Tasks />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/api" element={<Api />} />
                  <Route
                    path="*"
                    element={<Navigate to="/studies" />}
                  />
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
