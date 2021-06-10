/* eslint-disable react/destructuring-assignment */
import { Provider } from 'react-redux';
import React from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import { ThemeProvider } from '@material-ui/core/styles';
import { SnackbarProvider } from 'notistack';
import createStore from './reducers';
import { getConfig } from '../services/config';
import MenuBar from './MenuBar';
import StudyManagement from './Pages/StudyManagement';
import SingleStudyView from './Pages/SingleStudy';
import LoginWrapper from './LoginWrapper';
import theme, { TOOLBAR_HEIGHT } from './theme';
import SwaggerDoc from './Pages/SwaggerDoc';
import JobManagement from './Pages/JobManagement';
import UserSettings from './Pages/Settings'

const reduxStore = createStore();

const App: React.FC<{}> = () => (
  <Provider store={reduxStore}>
    <Router basename={getConfig().applicationHome}>
      <ThemeProvider theme={theme}>
        {getConfig().hidden && <Redirect to="/info" />}
        <SnackbarProvider maxSnack={5}>
          <div style={{ height: '100vh' }}>
            <LoginWrapper>
              <MenuBar />
              <div style={{ position: 'absolute', bottom: 0, width: '100%', overflow: 'hidden', top: TOOLBAR_HEIGHT }}>
                <Switch>
                  <Route path="/" exact key="home">
                    <StudyManagement />
                  </Route>
                  <Route path="/usersettings" exact key="usersettings">
                    <UserSettings />
                  </Route>
                  <Route path="/study/:studyId" key="module">
                    <SingleStudyView />
                  </Route>
                  <Route path="/jobs" key="module">
                    <JobManagement />
                  </Route>
                  <Route path="/swagger">
                    <SwaggerDoc />
                  </Route>
                </Switch>
              </div>
            </LoginWrapper>
          </div>
        </SnackbarProvider>
      </ThemeProvider>
    </Router>
  </Provider>
);

export default App;
