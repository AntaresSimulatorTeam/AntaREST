/* eslint-disable react/destructuring-assignment */
import { Provider } from 'react-redux';
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Switch, Redirect } from 'react-router-dom';
import { ThemeProvider } from '@material-ui/core/styles';
import debug from 'debug';
import createStore from './reducers';
import config from '../services/config';
import MenuBar from './MenuBar';
import StudyManagement from './Pages/StudyManagement';
import SingleStudyView from './Pages/SingleStudyView';
import AppLoader from '../components/ui/loaders/AppLoader';
import { initStudies } from '../ducks/study';
import { getStudies } from '../services/api/study';
import LoginWrapper from './LoginWrapper';
import theme, { TOOLBAR_HEIGHT } from './theme';

const logError = debug('antares:app:error');

const reduxStore = createStore();

const init = async (setLoaded: () => void) => {
  try {
    const studies = await getStudies();
    reduxStore.dispatch(initStudies(studies));
    setLoaded();
  } catch (e) {
    logError('woops', e);
  }
};

const App: React.FC<{}> = () => {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    init(() => setLoaded(true));
  }, []);

  if (!loaded) {
    return (
      <div style={{ height: '100vh', backgroundColor: theme.palette.primary.dark }}>
        <AppLoader />
      </div>
    );
  }

  return (
    <Provider store={reduxStore}>
      <Router basename={config.applicationHome}>
        <ThemeProvider theme={theme}>
          {config.hidden && <Redirect to="/info" />}
          <div style={{ height: '100vh' }}>
            <LoginWrapper>
              <MenuBar />
              <div style={{ position: 'absolute', bottom: 0, width: '100%', overflow: 'hidden', top: TOOLBAR_HEIGHT }}>
                <Switch>
                  <Route path="/" exact key="home">
                    <StudyManagement />
                  </Route>
                  <Route path="/study/:studyId" key="module">
                    <SingleStudyView />
                  </Route>
                </Switch>
              </div>
            </LoginWrapper>
          </div>
        </ThemeProvider>
      </Router>
    </Provider>
  );
};

export default App;
