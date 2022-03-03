import 'react-app-polyfill/ie11';
import 'react-app-polyfill/stable';
import React from 'react';
import ReactDOM from 'react-dom';
import { initI18n } from './i18n';
import './index.css';
import App from './App';
import * as serviceWorker from './serviceWorker';
import initFontAwesome from './services/utils/initFontAwesome';
import { Config, initConfig } from './services/config';
import { loadState, saveState } from './services/utils/localStorage';

initFontAwesome();
// eslint-disable-next-line react/no-render-return-value
initConfig((config: Config) => {
  const VERSION_INSTALLED_KEY = 'antaresweb.version';
  const versionInstalled = loadState(VERSION_INSTALLED_KEY);
  saveState(VERSION_INSTALLED_KEY, config.version.gitcommit);
  if (versionInstalled !== config.version.gitcommit) {
    // eslint-disable-next-line no-restricted-globals
    location.reload();
  }

  initI18n(config.version.gitcommit);

  ReactDOM.render(<App />, document.getElementById('root'));
});

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
