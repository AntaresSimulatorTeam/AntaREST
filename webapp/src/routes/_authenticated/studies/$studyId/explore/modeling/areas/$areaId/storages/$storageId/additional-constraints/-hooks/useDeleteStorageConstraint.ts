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
import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import { getNextItemAfterDeletion } from "@/utils/arrayUtils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { constraintsToList } from "../-utils";

function useDeleteStorageConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId, areaId, storageId } = params;
  const { queryKey: queryListKey } = storageQueries.constraintList(studyId, areaId, storageId);

  const mutation = useMutation({
    ...storageMutations.deleteConstraint(studyId, areaId, storageId),
    onMutate: async (variables) => {
      const { constraintId: constraintToDeleteId } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevConstraints = queryClient.getQueryData(queryListKey);
      const constraintToDelete = prevConstraints?.find((c) => c.id === constraintToDeleteId);

      if (constraintToDelete) {
        queryClient.setQueryData(queryListKey, (old) => {
          return old?.filter((constraint) => constraint.id !== constraintToDeleteId);
        });
      }

      const prevList = prevConstraints && constraintsToList(prevConstraints);

      const nextConstraint = prevList
        ? getNextItemAfterDeletion(
            prevList,
            prevList.findIndex((c) => c.id === constraintToDeleteId),
          )
        : undefined;

      router.navigate({
        to: nextConstraint
          ? "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId"
          : "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints",
        params: {
          ...params,
          constraintId: nextConstraint?.id,
        },
        replace: true,
      });

      return { constraintToDelete };
    },
    onError: (error, variables, onMutateResult) => {
      const { constraintId } = variables;
      const { constraintToDelete } = onMutateResult || {};

      if (constraintToDelete) {
        queryClient.setQueryData(queryListKey, (old = []) => [...old, constraintToDelete]);
      }

      enqueueErrorSnackbar(
        t("study.modeling.storages.additionalConstraints.delete.error", {
          name:
            queryClient.getQueryData(queryListKey)?.find((c) => c.id === constraintId)?.name ||
            constraintId,
        }),
        error,
      );
    },
  });

  return mutation;
}

export default useDeleteStorageConstraint;
