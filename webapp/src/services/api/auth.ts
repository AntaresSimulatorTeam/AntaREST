import axios from 'axios';
import querystring from 'querystring';
import moment from 'moment';
import jwt_decode from 'jwt-decode';
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
      const tokenData = jwt_decode(userInfoDTO.access_token);
      const userInfo : UserInfo  = {
        user: userInfoDTO.user,
        groups: (tokenData as any).sub.groups,
        id: (tokenData as any).sub.id,
        impersonator: (tokenData as any).sub.impersonator,
        type: (tokenData as any).sub.type,
        accessToken: userInfoDTO.access_token,
        refreshToken: userInfoDTO.refresh_token
      }
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
  const tokenData = jwt_decode(userInfo.access_token);
  const infos : UserInfo  = {
    user: userInfo.user,
    groups: (tokenData as any).sub.groups,
    id: (tokenData as any).sub.id,
    impersonator: (tokenData as any).sub.impersonator,
    type: (tokenData as any).sub.type,
    accessToken: userInfo.access_token,
    refreshToken: userInfo.refresh_token
  }
  return infos;
};

export default {};