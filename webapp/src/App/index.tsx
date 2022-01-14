/* eslint-disable react/destructuring-assignment */
import { Provider } from 'react-redux';
import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
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
import UserSettings from './Pages/Settings';
import Data from './Pages/Data';
import { addWsListeners } from '../services/utils/globalWsListeners';
import DownloadsManagement from './Pages/DownloadsManagement';
import MaintenanceWrapper from './MaintenanceWrapper';
import MessageInfoModal from './MaintenanceWrapper/MessageInfoModal';
import Logout from './Pages/Logout';

const reduxStore = createStore();
addWsListeners(reduxStore);

const App: React.FC<{}> = () => (
  <Provider store={reduxStore}>
    <Router basename={getConfig().applicationHome}>
      <ThemeProvider theme={theme}>
        <SnackbarProvider
          maxSnack={5}
        >
          <div style={{ height: '100vh' }}>
            <MaintenanceWrapper>
              <LoginWrapper>
                <MessageInfoModal />
                <MenuBar />
                <div style={{ position: 'absolute', bottom: 0, width: '100%', overflow: 'hidden', top: TOOLBAR_HEIGHT }}>
                  <Switch>
                    <Route path="/" exact key="home">
                      <StudyManagement />
                    </Route>
                    <Route path="/usersettings" exact key="usersettings">
                      <UserSettings />
                    </Route>
                    <Route path="/study/:studyId/:tab/:option" key="module">
                      <SingleStudyView />
                    </Route>
                    <Route exact path="/study/:studyId/:tab" key="module">
                      <SingleStudyView />
                    </Route>
                    <Route exact path="/study/:studyId/" key="module">
                      <SingleStudyView />
                    </Route>
                    <Route path="/jobs" key="module">
                      <JobManagement />
                    </Route>
                    <Route path="/data" key="data">
                      <Data />
                    </Route>
                    <Route path="/downloads" key="download">
                      <DownloadsManagement />
                    </Route>
                    <Route path="/swagger">
                      <SwaggerDoc />
                    </Route>
                    <Route path="/login" key="login">
                      <Logout />
                    </Route>
                  </Switch>
                </div>
              </LoginWrapper>
            </MaintenanceWrapper>
          </div>
        </SnackbarProvider>
      </ThemeProvider>
    </Router>
  </Provider>
);

export default App;
