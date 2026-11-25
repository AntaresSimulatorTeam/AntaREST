/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { isAxiosError } from "axios";
import client from "../client";
import { fileContentSchema, fileErrorSchema } from "./schemas";

/**
 * Reads original file bytes from a study file-content endpoint.
 *
 * @param url - User Resources or output file-content endpoint.
 * @param path - File path relative to the endpoint's root.
 * @param signal - Optional signal to cancel the request.
 * @returns The original file as a Blob.
 * @throws The request error with decoded server error details when available,
 * or a validation error if a successful response has an unexpected type.
 */
export async function getFileContent(
  url: string,
  path: string,
  signal?: AbortSignal,
): Promise<Blob> {
  try {
    const { data } = await client.get<Blob>(url, {
      params: { path },
      responseType: "blob",
      signal,
    });

    return fileContentSchema.parse(data);
  } catch (error) {
    const response = isAxiosError(error) ? error.response : undefined;

    // Axios returns JSON errors as Blobs too. Decode them so callers can read the server's description.
    if (response?.data instanceof Blob && response.data.type.split(";")[0] === "application/json") {
      try {
        response.data = fileErrorSchema.parse(JSON.parse(await response.data.text()));
      } catch {
        // Keep the original response when the server's error details cannot be decoded.
      }
    }

    throw error;
  }
}
