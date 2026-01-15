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
import { bindingConstraintMutations, bindingConstraintQueries } from "@/queries/bindingConstraints";
import { getNextItemAfterDeletion } from "@/utils/arrayUtils";
import { useMutation } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { bindingConstraintsToList } from "../-utils";

function useDeleteBindingConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/binding-constraints",
  });
  const router = useRouter();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId } = params;
  const { queryKey: queryListKey } = bindingConstraintQueries.list(studyId);

  const mutation = useMutation({
    ...bindingConstraintMutations.delete(),
    onMutate: async (variables, context) => {
      const { constraintId } = variables;

      await context.client.cancelQueries({ queryKey: queryListKey });

      const prevConstraints = context.client.getQueryData(queryListKey);

      context.client.setQueryData(queryListKey, (old) => {
        return old?.filter((constraint) => constraint.id !== constraintId);
      });

      const prevList = prevConstraints && bindingConstraintsToList(prevConstraints);

      const nextConstraint = prevList
        ? getNextItemAfterDeletion(
            prevList,
            prevList.findIndex((c) => c.id === constraintId),
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

      return { prevConstraints };
    },
    onError: (error, variables, onMutateResult, context) => {
      const { prevConstraints } = onMutateResult || {};
      const { constraintId } = variables;

      context.client.setQueryData(queryListKey, prevConstraints);

      enqueueErrorSnackbar(
        t("study.modeling.bindingConst.deleteBindingConstraint.error", {
          name:
            context.client.getQueryData(queryListKey)?.find((c) => c.id === constraintId)?.name ||
            constraintId,
        }),
        error,
      );
    },
    onSettled: (data, error, variables, onMutateResult, context) => {
      const mutationNb = context.client.isMutating({
        mutationKey: bindingConstraintMutations.all(),
      });

      if (mutationNb === 1) {
        context.client.invalidateQueries({ queryKey: queryListKey });
      }
    },
  });

  return mutation;
}

export default useDeleteBindingConstraint;
