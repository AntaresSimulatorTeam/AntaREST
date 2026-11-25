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

import { archiveOutput, deleteOutput, unarchiveOutput } from "@/services/api/studies/outputs";
import { materializeGemsViews } from "@/services/api/studies/outputs/gemsViews";
import type { GemsViewsState } from "@/services/api/studies/outputs/gemsViews/types";
import type { OutputParams } from "@/services/api/studies/outputs/types";
import type { Study } from "@/services/api/studies/types";
import { mutationOptions } from "@tanstack/react-query";
import { outputKeys } from "./keys";

export const outputMutations = {
  materializeGemsViews: (output: OutputParams) =>
    mutationOptions({
      mutationKey: outputKeys.materializeGemsViews(output),
      mutationFn: async (_variables: void, { client }) => {
        const metadata = { queryKey: outputKeys.gemsViews(output), exact: true };
        const taskId = await materializeGemsViews(output);

        if (taskId !== undefined) {
          const views = client.getQueryData<GemsViewsState>(metadata.queryKey);

          // A repeat response can arrive while the task's completion refetch is in flight.
          if (
            views?.status === "READY" ||
            (views?.status === "IN_PROGRESS" && views.taskId === taskId)
          ) {
            return taskId;
          }
        }

        await client.cancelQueries(metadata);

        if (taskId === undefined) {
          // HTTP 417 means the metadata is already available.
          await client.invalidateQueries(metadata);
        } else {
          client.setQueriesData<GemsViewsState>(metadata, (views) =>
            views?.status === "READY" ? undefined : { status: "IN_PROGRESS", taskId },
          );
        }

        return taskId;
      },
    }),
  delete: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.delete(studyId),
      mutationFn: async (output: OutputParams, { client }) => {
        await deleteOutput(output);
        client.removeQueries({ queryKey: outputKeys.detail(output) });
      },
    });
  },
  archive: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.archive(studyId),
      mutationFn: archiveOutput,
    });
  },
  unarchive: (studyId: Study["id"]) => {
    return mutationOptions({
      mutationKey: outputKeys.unarchive(studyId),
      mutationFn: unarchiveOutput,
    });
  },
};
