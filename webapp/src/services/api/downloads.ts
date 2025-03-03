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

import { getConfig } from "../config";
import client from "./client";

export interface FileDownloadDTO {
  id: string;
  name: string;
  filename: string;
  expiration_date: string;
  ready: boolean;
  failed: boolean;
  error_message: string;
}

export interface FileDownload {
  id: string;
  name: string;
  filename: string;
  expirationDate: string;
  ready: boolean;
  failed: boolean;
  errorMessage: string;
}

export interface FileDownloadTask {
  file: FileDownloadDTO;
  task: string;
}

export const convertFileDownloadDTO = (fileDownload: FileDownloadDTO): FileDownload => ({
  id: fileDownload.id,
  name: fileDownload.name,
  filename: fileDownload.filename,
  expirationDate: fileDownload.expiration_date,
  ready: fileDownload.ready,
  failed: fileDownload.failed,
  errorMessage: fileDownload.error_message,
});

export const getDownloadsList = async (): Promise<FileDownload[]> => {
  const res = await client.get("/v1/downloads");
  return res.data.map(convertFileDownloadDTO);
};

export const getDownloadUrl = (did: string): string =>
  `${getConfig().downloadHostUrl}/v1/downloads/${did}`;
