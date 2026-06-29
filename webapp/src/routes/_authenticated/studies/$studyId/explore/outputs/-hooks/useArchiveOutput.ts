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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { outputMutations } from "@/queries/outputs/mutations";
import { outputQueries } from "@/queries/outputs/queries";
import { createOptimisticListItem } from "@/queries/utils";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent, WsEventListener } from "@/services/webSocket/types";
import {
  addWsEventListener,
  removeWsEventListener,
  subscribeWsChannels,
  unsubscribeWsChannels,
} from "@/services/webSocket/ws";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useArchiveOutput() {
  const { studyId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/outputs/",
  });
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = outputQueries.list(studyId);

  let taskListener: WsEventListener | undefined;

  const mutation = useMutation({
    ...outputMutations.archive(studyId),
    onMutate: async (variables) => {
      const { outputId } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevOutputs = queryClient.getQueryData(queryListKey);
      const outputToArchive = prevOutputs?.find((output) => output.id === outputId);

      if (outputToArchive) {
        queryClient.setQueryData(queryListKey, (old = []) => {
          return old.map((output) =>
            output.id === outputId
              ? createOptimisticListItem({ ...output, archived: true })
              : output,
          );
        });
      }

      return { outputToArchive };
    },
    onSuccess: (taskId, variables, onMutateResult) => {
      const { outputId } = variables;
      const { outputToArchive } = onMutateResult || {};

      if (outputToArchive) {
        subscribeWsChannels(WsChannel.Task + taskId);

        // `mutationFn` run a task to archive the output, we need to wait for the task to complete
        // before updating the query cache by listening to the WebSocket events for the task.
        return new Promise<void>((resolve, reject) => {
          taskListener = (event: WsEvent) => {
            switch (event.type) {
              case WsEventType.TaskCompleted: {
                const { id } = event.payload;

                if (id === taskId) {
                  queryClient.setQueryData(queryListKey, (old = []) => {
                    return old.map((output) =>
                      output.id === outputId ? { ...outputToArchive, archived: true } : output,
                    );
                  });

                  resolve();
                }

                break;
              }
              case WsEventType.TaskFailed: {
                const { id, message } = event.payload;

                if (id === taskId) {
                  // `onError` will be called after this
                  reject(new Error(message));
                }

                break;
              }
            }
          };

          addWsEventListener(taskListener);
        });
      }
    },
    onError: (error, variables, onMutateResult) => {
      const { outputId } = variables;
      const { outputToArchive } = onMutateResult || {};

      if (outputToArchive) {
        queryClient.setQueryData(queryListKey, (old = []) =>
          old.map((output) => (output.id === outputId ? outputToArchive : output)),
        );
      }

      enqueueErrorSnackbar(
        t("studies.error.archiveOutput", {
          outputName:
            queryClient.getQueryData(queryListKey)?.find((o) => o.id === outputId)?.name ||
            outputId,
        }),
        error,
      );
    },
    onSettled: (taskId) => {
      if (taskId) {
        unsubscribeWsChannels(WsChannel.Task + taskId);
        if (taskListener) {
          removeWsEventListener(taskListener);
        }
      }
    },
  });

  return mutation;
}

export default useArchiveOutput;
