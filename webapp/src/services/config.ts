import debug from 'debug';

const info = debug('antares:config:info');

export interface Config {
  baseUrl: string;
  applicationHome: string;
  restEndpoint: string;
  wsEndpoint: string;
  wsUrl?: string;
  hidden: boolean;
  downloadHostUrl?: string;
}

const config: Config = {
  baseUrl: '',
  applicationHome: '',
  restEndpoint: '/',
  wsEndpoint: '/ws',
  hidden: false,
};

if (process.env.NODE_ENV === 'development') {
  config.applicationHome = '';
  config.baseUrl = 'http://localhost:3000';
  config.wsUrl = 'ws://localhost:8000';
  config.downloadHostUrl = 'http://localhost:8080';
  localStorage.setItem('debug', 'antares:*');
} else {
  config.baseUrl = `${window.location.origin}`;
//  config.hidden = true;
}

info('config is', config);

export default config;
