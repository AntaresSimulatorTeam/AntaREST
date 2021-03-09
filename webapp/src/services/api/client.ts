import axios, { AxiosResponse, AxiosRequestConfig } from 'axios';
import debug from 'debug';
import Cookies from 'js-cookie';
import { Config } from '../config';
import { UserInfo } from '../../common/types';

const logError = debug('antares:client:error');
const logInfo = debug('antares:client:info');

const client = axios.create();

export const setLogoutInterceptor = (logoutCallback: () => void): void => {
  client.interceptors.response.use(
    async (c): Promise<AxiosResponse> => c,
    async (e) => {
      logError('api error', e.response);
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
    Cookies.set('access_token_cookie', token);
  } else {
    delete client.defaults.headers.common.Authorization;
    Cookies.remove('access_token_cookie');
  }
};

let axiosInterceptor: number;
export const updateRefreshInterceptor = (refreshToken: () => Promise<UserInfo|undefined>): void => {
  logInfo('Updating refresh interceptor');
  if (axiosInterceptor !== undefined) {
    client.interceptors.request.eject(axiosInterceptor);
  }

  axiosInterceptor = client.interceptors.request.use(
    async (config): Promise<AxiosRequestConfig> => {
      try {
        const user = await refreshToken();
        if (user) {
          // eslint-disable-next-line no-param-reassign
          config.headers.Authorization = `Bearer ${user.accessToken}`;
        }
      } catch (e) {
        logError('Failed to refresh token', e);
      }
      return config;
    },
  );
};

export default client;
