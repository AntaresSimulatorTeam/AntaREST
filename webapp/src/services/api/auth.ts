/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import axios from "axios";
import client from "./client";
import type { RefreshDTO as UserTokensDTO } from "../../types/types";
import type { Config } from "../config";

// instance sans crédentials et hooks pour l'authent
const rawAxiosInstance = axios.create();

export const initRawAxiosClient = (config: Config): void => {
  rawAxiosInstance.defaults.baseURL = `${config.baseUrl}${config.restEndpoint}`;
};

export const needAuth = async (): Promise<boolean> => {
  try {
    const res = await client.get("/v1/auth");
    return res.data;
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
    },
  );
  return res.data;
};

export const login = async (username: string, password: string): Promise<UserTokensDTO> => {
  const res = await rawAxiosInstance.post("/v1/login", { username, password });
  return res.data;
};
