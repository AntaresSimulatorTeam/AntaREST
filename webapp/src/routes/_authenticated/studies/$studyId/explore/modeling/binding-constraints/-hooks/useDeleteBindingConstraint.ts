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
import { bindingConstraintMutations } from "@/queries/bindingConstraints/mutations";
import { bindingConstraintQueries } from "@/queries/bindingConstraints/queries";
import { getNextItemAfterDeletion } from "@/utils/arrayUtils";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { bindingConstraintsToList } from "../-utils";

function useDeleteBindingConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/binding-constraints",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId } = params;
  const { queryKey: queryListKey } = bindingConstraintQueries.list(studyId);

  const mutation = useMutation({
    ...bindingConstraintMutations.delete(studyId),
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

      const prevList = prevConstraints && bindingConstraintsToList(prevConstraints);

      const nextConstraint = prevList
        ? getNextItemAfterDeletion(
            prevList,
            prevList.findIndex((c) => c.id === constraintToDeleteId),
          )
        : undefined;

      router.navigate({
        to: nextConstraint
          ? "/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId"
          : "/studies/$studyId/explore/modeling/binding-constraints",
        params: {
          ...params,
          bindingConstraintId: nextConstraint?.id,
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
        t("study.modeling.bindingConst.deleteBindingConstraint.error", {
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

export default useDeleteBindingConstraint;
