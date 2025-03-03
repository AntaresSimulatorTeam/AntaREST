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

import { initAxiosClient } from "./api/client";
import { initRawAxiosClient } from "./api/auth";
import { getBackEndConfig, getVersionInfo } from "@/services/api/root";
import type { BackEndConfig, VersionInfoDTO } from "@/services/api/root/types";

const isDevEnv = process.env.NODE_ENV === "development";

export interface Config extends BackEndConfig {
  baseUrl: string;
  wsUrl: string;
  versionInfo: VersionInfoDTO;
  downloadHostUrl: string;
}

let config: Config = {
  baseUrl: window.location.origin,
  wsUrl: `ws${window.location.protocol === "https:" ? "s" : ""}://${window.location.host}`,
  downloadHostUrl: window.location.origin,
  restEndpoint: "",
  wsEndpoint: "/ws",
  versionInfo: {
    name: "unknown",
    version: "unknown",
    gitcommit: "unknown",
    dependencies: {},
  },
};

if (isDevEnv) {
  config = {
    ...config,
    baseUrl: "http://localhost:3000",
    wsUrl: "ws://localhost:8080",
    downloadHostUrl: "http://localhost:8080",
  };
}

export function getConfig(): Readonly<Config> {
  return config;
}

export async function initConfig() {
  try {
    const backendConfig = await getBackEndConfig();
    if (backendConfig) {
      config = {
        ...config,
        ...backendConfig,
        downloadHostUrl: getConfig().baseUrl + backendConfig.restEndpoint,
      };
    }
  } catch (err) {
    console.error(err);
  }

  initAxiosClient(config);
  initRawAxiosClient(config);

  try {
    config = {
      ...config,
      versionInfo: await getVersionInfo(),
    };
  } catch (err) {
    console.error(err);
  }

  return config;
}
