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
import { storageMutations, storageQueries } from "@/queries/storages";
import { useMutation } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

function useCreateStorageConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const router = useRouter();
  const tempConstraintId = useSafeMemo(() => crypto.randomUUID(), []);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId, areaId, storageId } = params;
  const queryOptions = storageQueries.constraintList(studyId, areaId, storageId);
  const { queryKey } = queryOptions;

  const isRouterMatchConstraint = (constraintId: string) => {
    return router.state.matches.some(
      (m) =>
        m.routeId ===
          "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId/" &&
        m.params.constraintId === constraintId,
    );
  };

  const mutation = useMutation({
    ...storageMutations.createConstraint(),
    meta: { tempConstraintId },
    onMutate: async (variables, context) => {
      const { values } = variables;

      await context.client.cancelQueries({ queryKey });

      const prevConstraints = context.client.getQueryData(queryKey);

      context.client.setQueryData(queryKey, (old = []) => {
        return [
          ...old,
          {
            ...values,
            id: tempConstraintId,
            name: values.name,
            variable: values.variable || "netting",
            operator: values.operator || "less",
            occurrences: values.occurrences || [],
            enabled: values.enabled ?? true,
            isOptimistic: true,
          },
        ];
      });

      // Await navigation prevents `onError`/`onSuccess` to be called before navigation is done,
      // causing `isRouterMatchConstraint(tempConstraintId)` to not work as expected
      await router.navigate({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId",
        params: { ...params, constraintId: tempConstraintId },
      });

      return { prevConstraints };
    },
    onError: (error, variables, onMutateResult, context) => {
      const { values } = variables;
      const { prevConstraints } = onMutateResult || {};

      context.client.setQueryData(queryKey, prevConstraints);

      enqueueErrorSnackbar(
        t("study.modeling.storages.additionalConstraints.create.error", { name: values.name }),
        error,
      );

      if (isRouterMatchConstraint(tempConstraintId)) {
        router.navigate({ to: "..", replace: true });
      }
    },
    onSuccess: (newConstraint, variables, onMutateResult, context) => {
      context.client.setQueryData(queryKey, (old = []) => {
        return old.map((constraint) =>
          constraint.id === tempConstraintId ? newConstraint : constraint,
        );
      });

      if (isRouterMatchConstraint(tempConstraintId)) {
        router.navigate({
          to: ".",
          params: { ...params, constraintId: newConstraint.id },
          replace: true,
        });
      }
    },
    onSettled: (data, error, variables, onMutateResult, context) => {
      context.client.invalidateQueries({ queryKey });
    },
  });

  return mutation;
}

export default useCreateStorageConstraint;
