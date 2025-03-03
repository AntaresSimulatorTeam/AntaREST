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

import type { AxiosRequestConfig } from "axios";
import client from "./client";
import type {
  MatrixDTO,
  MatrixDataSetDTO,
  MatrixInfoDTO,
  MatrixDataSetUpdateDTO,
  MatrixIndex,
  MatrixEditDTO,
} from "../../types/types";
import type { FileDownloadTask } from "./downloads";
import { getConfig } from "../config";
import type { MatrixUpdateDTO } from "../../components/common/Matrix/shared/types";

export const getMatrixList = async (name = "", filterOwn = false): Promise<MatrixDataSetDTO[]> => {
  const res = await client.get(
    `/v1/matrixdataset/_search?name=${encodeURI(name)}&filter_own=${filterOwn}`,
  );
  return res.data;
};

export const getMatrix = async (id: string): Promise<MatrixDTO> => {
  const res = await client.get(`/v1/matrix/${id}`);
  return res.data;
};

export const getExportMatrixUrl = (matrixId: string): string =>
  `${getConfig().downloadHostUrl}/v1/matrix/${matrixId}/download`;

export const exportMatrixDataset = async (datasetId: string): Promise<FileDownloadTask> => {
  const res = await client.get(`/v1/matrixdataset/${datasetId}/download`);
  return res.data;
};

export const createMatrixByImportation = async (
  file: File,
  json: boolean,
  onProgress?: (progress: number) => void,
): Promise<MatrixInfoDTO[]> => {
  const options: AxiosRequestConfig = {};
  if (onProgress) {
    options.onUploadProgress = (progressEvent): void => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / (progressEvent.total || 1),
      );
      onProgress(percentCompleted);
    };
  }
  const formData = new FormData();
  formData.append("file", file);
  const restconfig = {
    ...options,
    headers: {
      "content-type": "multipart/form-data",
    },
  };
  const res = await client.post(`/v1/matrix/_import?json=${json}`, formData, restconfig);
  return res.data;
};

export const createDataSet = async (
  metadata: MatrixDataSetUpdateDTO,
  matrices: MatrixInfoDTO[],
): Promise<MatrixDataSetDTO> => {
  const data = { metadata, matrices };
  const res = await client.post("/v1/matrixdataset", data);
  return res.data;
};

export const updateDataSet = async (
  id: string,
  metadata: MatrixDataSetUpdateDTO,
): Promise<MatrixDataSetUpdateDTO> => {
  const res = await client.put(`/v1/matrixdataset/${id}/metadata`, metadata);
  return res.data;
};

export const deleteDataSet = async (id: string): Promise<void> => {
  const res = await client.delete(`/v1/matrixdataset/${id}`);
  return res.data;
};

/**
 * @deprecated Use `updateMatrix` instead.
 *
 * @param sid - The study ID.
 * @param path - The path of the matrix.
 * @param matrixEdit - The matrix edit data.
 */
export const editMatrix = async (
  sid: string,
  path: string,
  matrixEdit: MatrixEditDTO[],
): Promise<void> => {
  const sanitizedPath = path.startsWith("/") ? path.substring(1) : path;

  await client.put(
    `/v1/studies/${sid}/matrix?path=${encodeURIComponent(sanitizedPath)}`,
    matrixEdit,
  );
};

export const updateMatrix = async (
  studyId: string,
  path: string,
  updates: MatrixUpdateDTO[],
): Promise<void> => {
  const sanitizedPath = path.startsWith("/") ? path.substring(1) : path;

  await client.put(
    `/v1/studies/${studyId}/matrix?path=${encodeURIComponent(sanitizedPath)}`,
    updates,
  );
};

export const getStudyMatrixIndex = async (sid: string, path?: string): Promise<MatrixIndex> => {
  const query = path ? `?path=${encodeURIComponent(path)}` : "";
  const res = await client.get(`/v1/studies/${sid}/matrixindex${query}`);
  return res.data;
};
