import axios from 'axios';
import querystring from 'querystring';
import client from './client';
import { UserInfo } from '../../common/types';
import config from '../config';

// instance sans crédentials et hooks pour l'authent
const rawAxiosInstance = axios.create();
rawAxiosInstance.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
rawAxiosInstance.interceptors.request.use((axiosConfig) => {
  const cleanConfig = { ...axiosConfig };
  cleanConfig.headers.Authorization = '';
  return cleanConfig;
});

export const needAuth = async (): Promise<boolean> => {
  try {
    await client.get('/users');
    return Promise.resolve(false);
  } catch (e) {
    const { status } = e.response;
    if (status === 401) {
      return Promise.resolve(true);
    }
    throw e;
  }
};

export async function login(
  username: string,
  password: string,
): Promise<UserInfo> {
  const data = querystring.stringify({ username, password });
  const res = await rawAxiosInstance.post('/login', data, { headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
  } });
  return res.data;
}

export default {};
