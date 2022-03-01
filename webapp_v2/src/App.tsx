import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
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
                  <Route path="/studies" element={<Studies />} />
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
