import axios from 'axios';
import querystring from 'querystring';
import moment from 'moment';
import client from './client';
import { UserInfo } from '../../common/types';
import { Config } from '../config';


// instance sans crédentials et hooks pour l'authent
const rawAxiosInstance = axios.create();

export const initRawAxiosClient = (config: Config): void => {
  rawAxiosInstance.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
};

export const needAuth = async (): Promise<boolean> => {
  try {
    await client.get('/auth');
    return Promise.resolve(false);
  } catch (e) {
    const { status } = e.response;
    if (status === 401) {
      return Promise.resolve(true);
    }
    throw e;
  }
};

export const refresh = async (user: UserInfo, login: (user: UserInfo) => void, logout: () => void): Promise<UserInfo|undefined> => {
  if (!user.expirationDate || user.expirationDate < moment().add(5, 's')) {
    try {
      const res = await rawAxiosInstance.post('/refresh', {}, { headers: {
        Authorization: `Bearer ${user.refreshToken}`,
      } });
      const userInfoDTO = await res.data;
      const userInfo = { user: userInfoDTO.user, accessToken: userInfoDTO.access_token, refreshToken: userInfoDTO.refresh_token };
      login(userInfo);
      return userInfo;
    } catch (e) {
      logout();
    }
    return undefined;
  }
};

export const login = async (
  username: string,
  password: string,
): Promise<UserInfo> => {
  const data = querystring.stringify({ username, password });
  const res = await rawAxiosInstance.post('/login', data, { headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  } });
  const userInfo = await res.data;
  return { user: userInfo.user, accessToken: userInfo.access_token, refreshToken: userInfo.refresh_token };
};

export default {};
