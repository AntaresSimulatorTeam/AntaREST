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

import { getOutputs } from "@/services/api/studies/outputs";
import { getGemsViews } from "@/services/api/studies/outputs/gemsViews";
import { getOutputFileContent, getOutputFilesTree } from "@/services/api/studies/outputs/rawFiles";
import type { OutputFileParams } from "@/services/api/studies/outputs/rawFiles/types";
import type { OutputParams } from "@/services/api/studies/outputs/types";
import type { Study } from "@/services/api/studies/types";
import { queryOptions } from "@tanstack/react-query";
import { DEFAULT_STALE_TIME_MS } from "../queryClient";
import { queryListOptions } from "../utils";
import { outputKeys } from "./keys";

export const outputQueries = {
  list: (studyId: Study["id"]) => {
    return queryListOptions({
      queryKey: outputKeys.list(studyId),
      queryFn: () => getOutputs({ studyId }),
    });
  },
  gemsViews: (output: OutputParams) =>
    queryOptions({
      queryKey: outputKeys.gemsViews(output),
      queryFn: ({ signal }) => getGemsViews(output, signal),
      staleTime: ({ state }) => (state.data?.status === "READY" ? DEFAULT_STALE_TIME_MS : 0),
    }),
  rawFiles: (output: OutputParams) =>
    queryOptions({
      queryKey: outputKeys.rawFiles(output),
      queryFn: ({ signal }) => getOutputFilesTree(output, signal),
    }),
  rawFileContent: (file: OutputFileParams) =>
    queryOptions({
      queryKey: outputKeys.rawFileContent(file),
      queryFn: ({ signal }) => getOutputFileContent(file, signal),
      // Keep the original bytes for as long as the file is open.
      staleTime: Infinity,
      gcTime: 0,
    }),
};
