import axios from "axios";
import debug from "debug";
import Cookies from "js-cookie";
import * as R from "ramda";
import { Config } from "../config";
import store from "../../redux/store";
import { logout, refresh } from "../../redux/ducks/auth";

const logError = debug("antares:client:error");
const logInfo = debug("antares:client:info");

let axiosInterceptor: number;

function makeHeaderAuthorization(token: string): string {
  return `Bearer ${token}`;
}

const client = axios.create();

export function initAxiosClient(config: Config): void {
  client.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
}

export function initAxiosInterceptors(): void {
  // Intercept requests and responses before they are handled by then or catch

  client.interceptors.response.use(R.identity, (err) => {
    logError("API error", err);
    if (axios.isAxiosError(err)) {
      if (err.response?.status === 401) {
        store.dispatch(logout()); // `setAuth()` is called inside
      }
    }
    return Promise.reject(err);
  });

  logInfo("Updating refresh interceptor");
  if (axiosInterceptor !== undefined) {
    client.interceptors.request.eject(axiosInterceptor);
  }

  axiosInterceptor = client.interceptors.request.use(async (config) => {
    try {
      if (config?.headers) {
        const authUser = await store.dispatch(refresh()).unwrap();
        if (authUser) {
          // eslint-disable-next-line no-param-reassign
          config.headers.Authorization = makeHeaderAuthorization(
            authUser.accessToken
          );
        }
      }
    } catch (e) {
      logError("Failed to refresh token", e);
    }
    return config;
  });
}

export function setAuth(token: string | null): void {
  if (token) {
    client.defaults.headers.common.Authorization =
      makeHeaderAuthorization(token);
    Cookies.set("access_token_cookie", token);
  } else {
    delete client.defaults.headers.common.Authorization;
    if (axiosInterceptor !== undefined) {
      client.interceptors.request.eject(axiosInterceptor);
    }
    Cookies.remove("access_token_cookie");
  }
}

export default client;
