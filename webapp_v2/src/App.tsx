import React from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from 'react-router-dom';
import { CssBaseline, styled, ThemeProvider } from '@mui/material';
import { SnackbarProvider } from 'notistack';
import maintheme from './theme';
import LogginWrapper from './pages/wrappers/LogginWrapper';
import MenuWrapper from './pages/wrappers/MenuWrapper';
import Studies from './pages/Studies';
import Data from './pages/Data';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Api from './pages/Api';

function App() {
  return (
    <Router>
      <ThemeProvider theme={maintheme}>
        <SnackbarProvider maxSnack={5}>
          <CssBaseline />
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
        </SnackbarProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
