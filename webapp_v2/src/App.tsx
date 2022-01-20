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

const Root = styled('div')({
  width: '100vw',
  height: '100vh',
  minWidth: '280px',
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'flex-start',
  boxSizing: 'border-box',
  backgroundColor: 'blue',
});

function App() {
  return (
    <Router>
      <ThemeProvider theme={maintheme}>
        <SnackbarProvider maxSnack={5}>
          <CssBaseline />
          <LogginWrapper>
            <MenuWrapper>
              <Routes>
                <Route index element={<Studies />} />
                <Route path="/studies" element={<Studies />} />
                <Route path="/data" element={<Data />} />
                <Route path="/tasks" element={<Tasks />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/api" element={<Api />} />
                <Route
                  path="*"
                  element={<Navigate to="/" />}
                />
              </Routes>
            </MenuWrapper>
          </LogginWrapper>
        </SnackbarProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
