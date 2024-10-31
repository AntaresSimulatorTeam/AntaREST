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
import type {
  DeleteFileParams,
  DownloadMatrixParams,
  ImportFileParams,
} from "./types";

export async function downloadMatrix(params: DownloadMatrixParams) {
  const { studyId, ...queryParams } = params;
  const url = `v1/studies/${studyId}/raw/download`;

  const res = await client.get<Blob>(url, {
    params: queryParams,
    responseType: "blob",
  });

  return res.data;
}

export async function importFile(params: ImportFileParams) {
  const { studyId, file, onUploadProgress, ...queryParams } = params;
  const url = `v1/studies/${studyId}/raw`;
  const body = { file };

  await client.putForm<void>(url, body, {
    params: {
      ...queryParams,
      create_missing: queryParams.createMissing,
    },
    onUploadProgress,
  });
}

export async function deleteFile(params: DeleteFileParams) {
  const { studyId, path } = params;
  const url = `v1/studies/${studyId}/raw`;

  await client.delete<void>(url, { params: { path } });
}
