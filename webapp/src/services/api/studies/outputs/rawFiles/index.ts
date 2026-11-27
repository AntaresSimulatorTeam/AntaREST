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

import client from "@/services/api/client";
import { getFileContent } from "@/services/api/files";
import { filesTreeSchema } from "@/services/api/files/schemas";
import type { FilesTree } from "@/services/api/files/types";
import type { OutputParams } from "../types";
import type { OutputFileParams } from "./types";

/**
 * GET /v1/studies/{studyId}/outputs/{outputId}/raw-files - Lists the files in an output.
 *
 * @param params - Output to browse.
 * @param params.studyId - Study identifier.
 * @param params.outputId - Output identifier.
 * @param signal - Optional signal to cancel the request.
 * @returns The tree of files relative to the output root.
 * @throws If the response does not match the file-tree schema.
 */
export async function getOutputFilesTree(
  { studyId, outputId }: OutputParams,
  signal?: AbortSignal,
): Promise<FilesTree> {
  const { data } = await client.get(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/raw-files`,
    { signal },
  );

  return filesTreeSchema.parse(data);
}

/**
 * GET /v1/studies/{studyId}/outputs/{outputId}/raw-files/content - Reads an original output file.
 *
 * @param params - File to read.
 * @param params.studyId - Study identifier.
 * @param params.outputId - Output identifier.
 * @param params.path - File path relative to the output root.
 * @param signal - Optional signal to cancel the request.
 * @returns The file's original bytes.
 * @throws If the response is not a Blob.
 */
export function getOutputFileContent(
  { studyId, outputId, path }: OutputFileParams,
  signal?: AbortSignal,
): Promise<Blob> {
  return getFileContent(
    `/v1/studies/${studyId}/outputs/${encodeURIComponent(outputId)}/raw-files/content`,
    path,
    signal,
  );
}
