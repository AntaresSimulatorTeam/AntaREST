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
import useSafeMemo from "@/hooks/useSafeMemo";
import { bindingConstraintMutations } from "@/queries/bindingConstraints/mutations";
import { bindingConstraintQueries } from "@/queries/bindingConstraints/queries";
import type { QueryListItem } from "@/queries/types";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES } from "../-utils";

function useDuplicateBindingConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/binding-constraints",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const tempConstraintId = useSafeMemo(() => crypto.randomUUID(), []);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId } = params;
  const { queryKey: queryListKey } = bindingConstraintQueries.list(studyId);

  const isRouterMatchTempConstraint = () => {
    return router.state.matches.some(
      (m) =>
        m.routeId ===
          "/_authenticated/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId" &&
        m.params.bindingConstraintId === tempConstraintId,
    );
  };

  const mutation = useMutation({
    ...bindingConstraintMutations.duplicate(studyId),
    onMutate: async (variables) => {
      const { constraintId: constraintToDuplicateId, newConstraintName } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      const prevConstraints = queryClient.getQueryData(queryListKey);
      const constraintToDuplicate = prevConstraints?.find((c) => c.id === constraintToDuplicateId);

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          {
            ...DEFAULT_CONSTRAINT_VALUES,
            ...constraintToDuplicate,
            id: tempConstraintId,
            name: newConstraintName,
            _metadata: { isOptimistic: true },
          } satisfies QueryListItem<BindingConstraint>,
        ];
      });

      // Await navigation prevents `onError`/`onSuccess` to be called before navigation is done,
      // causing `isRouterMatchTempConstraint()` to not work as expected
      await router.navigate({
        to: "/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId",
        params: { ...params, bindingConstraintId: tempConstraintId },
      });
    },
    onError: (error, variables) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((constraint) => constraint.id !== tempConstraintId);
      });

      enqueueErrorSnackbar(
        t("study.modeling.bindingConst.duplicate.error", { name: variables.newConstraintName }),
        error,
      );

      if (isRouterMatchTempConstraint()) {
        router.navigate({
          to: "/studies/$studyId/explore/modeling/binding-constraints",
          params,
          replace: true,
        });
      }
    },
    onSuccess: (newConstraint) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((constraint) =>
          constraint.id === tempConstraintId ? newConstraint : constraint,
        );
      });

      if (isRouterMatchTempConstraint()) {
        router.navigate({
          to: ".",
          params: { ...params, bindingConstraintId: newConstraint.id },
          replace: true,
        });
      }
    },
  });

  return mutation;
}

export default useDuplicateBindingConstraint;
