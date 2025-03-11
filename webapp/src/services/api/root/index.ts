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

import client from "@/services/api/client";
import type { BackEndConfig, VersionInfoDTO } from "@/services/api/root/types";
import axios from "axios";

export async function getBackEndConfig() {
  // `client` is not used, because this endpoint is used to configure its base URL.
  // Apparently, `BackEndConfig` is only send for the desktop app, otherwise 'index.html' file content is send.
  // This is a strange behavior that need to be fixed (cf. antarest/front.py).
  const { data } = await axios.get<BackEndConfig | string>("/config.json");
  return typeof data === "string" ? null : data;
}

export async function getVersionInfo() {
  const { data } = await client.get<VersionInfoDTO>("/version");
  return data;
}
