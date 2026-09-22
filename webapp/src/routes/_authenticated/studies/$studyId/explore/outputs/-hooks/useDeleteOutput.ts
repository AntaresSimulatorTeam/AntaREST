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
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useDeleteOutput() {
  const { studyId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/outputs/",
  });
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { queryKey: queryListKey } = outputQueries.list(studyId);

  const mutation = useMutation({
    ...outputMutations.delete(studyId),
    onMutate: async (variables) => {
      const { outputId: outputToDeleteId } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevOutputs = queryClient.getQueryData(queryListKey);
      const outputToDelete = prevOutputs?.find((output) => output.id === outputToDeleteId);

      if (outputToDelete) {
        queryClient.setQueryData(queryListKey, (old) => {
          return old?.filter((output) => output.id !== outputToDeleteId);
        });
      }

      return { outputToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { outputId } = variables;
      const { outputToDelete } = onMutateResult || {};

      if (outputToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, outputToDelete]);
      }

      enqueueErrorSnackbar(
        t("study.outputs.delete.error", {
          outputName:
            outputToDelete?.name ||
            queryClient.getQueryData(queryListKey)?.find((o) => o.id === outputId)?.name ||
            outputId,
        }),
        error,
      );
    },
  });

  return mutation;
}

export default useDeleteOutput;
