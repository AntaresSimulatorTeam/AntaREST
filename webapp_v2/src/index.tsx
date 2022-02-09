import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { StyledEngineProvider } from '@mui/material';
import createStore from './store/reducers';
import { addWsListeners } from './services/utils/globalWsListeners';
import './i18n';
import './index.css';
import App from './App';

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
