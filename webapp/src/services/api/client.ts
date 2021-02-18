import axios, { AxiosResponse } from 'axios';
import debug from 'debug';
import { Config } from '../config';

const error = debug('antares:client:error');

const client = axios.create();

export const setAxiosInterceptor = (logoutCallback: () => void): void => {
  client.interceptors.response.use(
    async (c): Promise<AxiosResponse> => c,
    async (e) => {
      error('api error', e.response);
      const { status } = e.response;
      if (e && status === 401) {
        client.defaults.headers.common.Authorization = null;
        logoutCallback();
      }
      return Promise.reject(e);
    },
  );
};

export const initAxiosClient = (config: Config): void => {
  client.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
};

export const setAuth = (token: string | undefined): void => {
  if (token) {
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete client.defaults.headers.common.Authorization;
  }
};

export default client;
