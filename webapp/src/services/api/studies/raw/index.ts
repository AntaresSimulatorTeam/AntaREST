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
import type {
  DeleteFileParams,
  DownloadMatrixParams,
  ImportFileParams,
  RawFile,
} from "./types";

export async function downloadMatrix(params: DownloadMatrixParams) {
  const { studyId, ...queryParams } = params;
  const url = `/v1/studies/${studyId}/raw/download`;

  const { data } = await client.get<Blob>(url, {
    params: queryParams,
    responseType: "blob",
  });

  return data;
}

export async function importFile(params: ImportFileParams) {
  const { studyId, file, onUploadProgress, ...queryParams } = params;
  const url = `/v1/studies/${studyId}/raw`;
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
  const url = `/v1/studies/${studyId}/raw`;

  await client.delete<void>(url, { params: { path } });
}

/**
 * Reads an original raw file from a study with its metadata.
 *
 * @param studyId - Unique identifier of the study
 * @param filePath - Path to the file within the study
 * @returns Promise containing the file data and metadata
 */
export async function getRawFile(
  studyId: string,
  filePath: string,
): Promise<RawFile> {
  const response = await client.get(
    `/v1/studies/${studyId}/raw/original-file`,
    {
      params: {
        path: filePath,
      },
      responseType: "blob",
    },
  );

  const contentDisposition = response.headers["content-disposition"];
  let filename = filePath.split("/").pop() || "file"; // fallback filename

  if (contentDisposition) {
    const matches = /filename=([^;]+)/.exec(contentDisposition);
    if (matches?.[1]) {
      filename = matches[1].replace(/"/g, "").trim();
    }
  }

  return {
    data: response.data,
    filename: filename,
  };
}
