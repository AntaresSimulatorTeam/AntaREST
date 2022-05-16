/* eslint-disable camelcase */
import axios from "axios";
import client from "./client";
import { RefreshDTO as UserTokensDTO } from "../../common/types";
import { Config } from "../config";

// instance sans crédentials et hooks pour l'authent
const rawAxiosInstance = axios.create();

export const initRawAxiosClient = (config: Config): void => {
  rawAxiosInstance.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
};

export const needAuth = async (): Promise<boolean> => {
  try {
    await client.get("/v1/auth");
    return false;
  } catch (e) {
    if (axios.isAxiosError(e)) {
      if (e.response?.status === 401) {
        return true;
      }
    }
    throw e;
  }
};

export const refresh = async (refreshToken: string): Promise<UserTokensDTO> => {
  const res = await rawAxiosInstance.post(
    "/v1/refresh",
    {},
    {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    }
  );
  return res.data;
};

export const login = async (
  username: string,
  password: string
): Promise<UserTokensDTO> => {
  const res = await rawAxiosInstance.post("/v1/login", { username, password });
  return res.data;
};
