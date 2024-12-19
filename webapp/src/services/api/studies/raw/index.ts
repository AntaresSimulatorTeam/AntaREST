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
  GetMatrixFileParams,
  RawFile,
  UploadFileParams,
} from "./types";

/**
 * Reads a matrix file from a study's raw files.
 *
 * @param params - Parameters for reading the matrix
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Path to the matrix file
 * @param params.format - Optional export format for the matrix
 * @param params.header - Whether to include headers
 * @param params.index - Whether to include indices
 * @returns Promise containing the matrix data as a Blob
 */
export async function getMatrixFile(
  params: GetMatrixFileParams,
): Promise<Blob> {
  const { studyId, ...queryParams } = params;

  const { data } = await client.get<Blob>(
    `/v1/studies/${studyId}/raw/download`,
    {
      params: queryParams,
      responseType: "blob",
    },
  );
  return data;
}

/**
 * Uploads a file to a study's raw storage, creating or updating it based on existence.
 *
 * !Note: This method currently uses a poorly named endpoint (/raw). The endpoint structure
 * should be refactored to follow REST principles:
 * - PUT /raw/files/{path}/content - Upload file content (multipart/form-data, large files) `uploadFile`
 * - PATCH /raw/files/{path} - Update existing file (for metadata or small content changes) `updateFile`
 * - POST /raw/files - Create new file (system generates path) `createFile`
 * - GET /raw/files/{path} - Retrieve file `getFile`
 * - DELETE /raw/files/{path} - Delete file `deleteFile`
 *
 * PUT is used for upload since we're updating a resource at a known path, whether
 * it exists or not (idempotent operation).
 *
 * TODO:
 * 1. Migrate to the new REST endpoints structure
 * 2. Remove createMissing param and handle directory creation automatically
 *
 * @param params - Parameters for the file upload
 * @param params.studyId - Unique identifier of the study
 * @param params.path - Destination path for the file
 * @param params.file - File content to upload
 * @param params.createMissing - Whether to create missing parent directories
 * @param params.onUploadProgress - Callback for upload progress updates
 * @returns Promise that resolves when the upload is complete
 */
export async function uploadFile(params: UploadFileParams): Promise<void> {
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
export async function deleteFile(params: DeleteFileParams): Promise<void> {
  const { studyId, path } = params;
  await client.delete(`/v1/studies/${studyId}/raw`, { params: { path } });
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
  const { data, headers } = await client.get<RawFile["data"]>(
    `/v1/studies/${studyId}/raw/original-file`,
    {
      params: {
        path: filePath,
      },
      responseType: "blob",
    },
  );

  // Get the original file name from the response Headers
  const contentDisposition = headers["content-disposition"];
  let filename = filePath.split("/").pop() || "file"; // fallback filename

  if (contentDisposition) {
    const matches = /filename=([^;]+)/.exec(contentDisposition);

    if (matches?.[1]) {
      filename = matches[1].replace(/"/g, "").trim();
    }
  }

  return {
    data,
    filename,
  };
}
