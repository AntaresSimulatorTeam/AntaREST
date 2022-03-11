import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { StyledEngineProvider } from '@mui/material';
import createStore from './store/reducers';
import { addWsListeners } from './services/utils/globalWsListeners';
import { initI18n } from './i18n';
import './index.css';
import App from './App';
import { Config, initConfig } from './services/config';
import { loadState, saveState } from './services/utils/localStorage';

initConfig((config: Config) => {
  const VERSION_INSTALLED_KEY = 'antaresweb.version';
  const versionInstalled = loadState(VERSION_INSTALLED_KEY);
  saveState(VERSION_INSTALLED_KEY, config.version.gitcommit);
  if (versionInstalled !== config.version.gitcommit) {
    // eslint-disable-next-line no-restricted-globals
    location.reload();
  }

  initI18n(config.version.gitcommit);

  const reduxStore = createStore();
  addWsListeners(reduxStore);

  ReactDOM.render(
    <StyledEngineProvider injectFirst>
      <Provider store={reduxStore}>
        <App />
      </Provider>
    </StyledEngineProvider>,
    document.getElementById('root'),
  );
});
