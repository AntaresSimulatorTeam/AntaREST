import 'react-app-polyfill/ie11';
import 'react-app-polyfill/stable';
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import * as serviceWorker from './serviceWorker';
import './i18n';
import initFontAwesome from './services/utils/initFontAwesome';
import { initConfig } from './services/config';

initFontAwesome();

// eslint-disable-next-line react/no-render-return-value
initConfig(() => ReactDOM.render(<App />, document.getElementById('root')));

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
