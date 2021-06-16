import debug from 'debug';
import axios from 'axios';
import { initAxiosClient } from './api/client';
import { initRawAxiosClient } from './api/auth';

const info = debug('antares:config:info');
const warn = debug('antares:config:warn');

export interface Config {
  baseUrl: string;
  applicationHome: string;
  restEndpoint: string;
  wsUrl: string;
  wsEndpoint: string;
  hidden: boolean;
  downloadHostUrl?: string;
}

let config: Config = {
  baseUrl: '',
  applicationHome: '',
  restEndpoint: '',
  wsUrl: '',
  wsEndpoint: '/ws',
  hidden: false,
};

if (process.env.NODE_ENV === 'development') {
  config.applicationHome = '';
  config.baseUrl = 'http://localhost:3000';
  config.wsUrl = 'ws://localhost:8080';
  config.downloadHostUrl = 'http://localhost:8080';
  localStorage.setItem('debug', 'antares:*');
} else {
  config.baseUrl = `${window.location.origin}`;
  config.wsUrl = `ws${window.location.protocol === 'https:' ? 's' : ''}://${window.location.host}`;
//  config.hidden = true;
}

export const getConfig = (): Config => config;

export const initConfig = async (callback: any): Promise<void> => {
  try {
    const res = await axios.get('/config.json', { baseURL: '/' });
    config = {
      ...config,
      ...res.data,
    };
  } catch (e) {
    warn('Failed to retrieve site config. Will use default env configuration.');
  }

  info('config is', config);

  initAxiosClient(config);
  initRawAxiosClient(config);

  callback();
};
