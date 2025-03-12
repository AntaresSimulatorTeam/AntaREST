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

import client from "../../client";
import type {
  CreateFolderParams,
  DeleteFileParams,
  GetMatrixFileParams,
  GetRawFileParams,
  UploadFileParams,
} from "./types";

/**
 * Gets a matrix file from a study's raw files.
 *
 * @param params - Parameters for getting the matrix
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Path to the matrix file
 * @param params.format - Optional. Export format for the matrix
 * @param params.header - Optional. Whether to include headers
 * @param params.index - Optional. Whether to include indices
 * @returns Promise containing the matrix data as a Blob
 */
export async function getMatrixFile(params: GetMatrixFileParams) {
  const { studyId, ...queryParams } = params;

  const { data } = await client.get<Blob>(`/v1/studies/${studyId}/raw/download`, {
    params: queryParams,
    responseType: "blob",
  });
  return data;
}

/**
 * Uploads a file to a study's raw storage, creating or updating it based on existence.
 *
 * !Warning: This endpoint currently uses a non-standard REST structure (/raw) which
 * may lead to confusion. It handles both create and update operations through PUT,
 * while directory creation is managed through a separate flag.
 *
 * @param params - Parameters for the file upload
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Destination path for the file
 * @param params.file - File content to upload
 * @param params.createMissing - Optional. Whether to create missing parent directories
 * @param params.onUploadProgress - Optional. Callback for upload progress updates
 * @returns Promise that resolves when the upload is complete
 */
export async function uploadFile(params: UploadFileParams) {
  const { studyId, file, onUploadProgress, ...queryParams } = params;
  const body = { file };

  await client.putForm(`/v1/studies/${studyId}/raw`, body, {
    params: {
      ...queryParams,
      create_missing: queryParams.createMissing,
    },
    onUploadProgress,
  });
}

/**
 * Deletes a raw file from a study.
 *
 * @param params - Parameters for deleting the file
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Path to the file to delete
 * @returns Promise that resolves when the deletion is complete
 */
export async function deleteFile({ studyId, path }: DeleteFileParams) {
  await client.delete(`/v1/studies/${studyId}/raw`, { params: { path } });
}

/**
 * Gets an original raw file from a study with its metadata.
 *
 * @param params - Parameters for getting the raw file and name
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Path to the file within the study
 * @returns Promise containing the file data and metadata
 */
export async function getRawFile({ studyId, path }: GetRawFileParams) {
  const { data, headers } = await client.get<File>(`/v1/studies/${studyId}/raw/original-file`, {
    params: {
      path,
    },
    responseType: "blob",
  });

  // Get the original file name from the response Headers
  const contentDisposition = headers["content-disposition"];
  let filename = path.split("/").pop() || "file"; // fallback filename

  if (contentDisposition) {
    const matches = /filename=([^;]+)/.exec(contentDisposition);

    if (matches?.[1]) {
      filename = matches[1].replace(/"/g, "").trim();
    }
  }

  return new File([data], filename, {
    type: data.type, // Preserve the MIME type from the Blob
    lastModified: new Date().getTime(),
  });
}

export async function createFolder({ studyId, path }: CreateFolderParams) {
  await client.put(`/v1/studies/${studyId}/raw`, null, {
    params: {
      path,
      create_missing: true,
      resource_type: "folder",
    },
  });
}
