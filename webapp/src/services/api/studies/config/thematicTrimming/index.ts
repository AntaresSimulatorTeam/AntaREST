/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import { format } from "@/utils/stringUtils";

import type {
  GetThematicTrimmingConfigParams,
  SetThematicTrimmingConfigParams,
  ThematicTrimmingConfig,
} from "./types";

const URL = "/v1/studies/{studyId}/config/thematictrimming/form";

export async function getThematicTrimmingConfig({
  studyId,
}: GetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  const res = await client.get<ThematicTrimmingConfig>(url);
  return res.data;
}

export async function setThematicTrimmingConfig({
  studyId,
  config,
}: SetThematicTrimmingConfigParams) {
  const url = format(URL, { studyId });
  await client.put(url, config);
}
