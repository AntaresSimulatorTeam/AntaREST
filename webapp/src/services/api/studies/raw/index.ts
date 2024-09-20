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

import client from "../../client";
import type { DownloadMatrixParams } from "./types";

export async function downloadMatrix(params: DownloadMatrixParams) {
  const { studyId, ...rest } = params;
  const url = `v1/studies/${studyId}/raw/download`;
  const res = await client.get<Blob>(url, {
    params: rest,
    responseType: "blob",
  });

  return res.data;
}
