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
import { outputKeys } from "@/queries/outputs/keys";
import { outputMutations } from "@/queries/outputs/mutations";
import { outputQueries } from "@/queries/outputs/queries";
import { createOptimisticListItem } from "@/queries/utils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { waitForOutputArchiveTask } from "../-utils";

function useArchiveOutput() {
  const { studyId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/outputs/",
  });
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = outputQueries.list(studyId);

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
    onSuccess: async (taskId, output, onMutateResult) => {
      const { outputToArchive } = onMutateResult || {};

      await waitForOutputArchiveTask(queryClient, taskId);
      queryClient.removeQueries({ queryKey: outputKeys.detail(output) });

      if (outputToArchive) {
        queryClient.setQueryData(queryListKey, (old = []) =>
          old.map((item) =>
            item.id === output.outputId ? { ...outputToArchive, archived: true } : item,
          ),
        );
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
  });

  return mutation;
}

export default useArchiveOutput;
