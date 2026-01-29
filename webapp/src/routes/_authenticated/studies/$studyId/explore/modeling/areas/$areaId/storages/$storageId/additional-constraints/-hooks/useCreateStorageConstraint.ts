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
import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import type { QueryListItem } from "@/queries/types";
import type { StorageConstraint } from "@/services/api/studies/areas/storages/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES } from "../-constants";

function useCreateStorageConstraint() {
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const router = useRouter();
  const queryClient = useQueryClient();
  const tempConstraintId = useSafeMemo(() => crypto.randomUUID(), []);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  const { studyId, areaId, storageId } = params;
  const { queryKey: queryListKey } = storageQueries.constraintList(studyId, areaId, storageId);

  const isRouterMatchTempConstraint = () => {
    return router.state.matches.some(
      (m) =>
        m.routeId ===
          "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId/" &&
        m.params.constraintId === tempConstraintId,
    );
  };

  const mutation = useMutation({
    ...storageMutations.createConstraint(studyId, areaId, storageId),
    onMutate: async (variables) => {
      const { values } = variables;

      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) => {
        return [
          ...old,
          {
            ...DEFAULT_CONSTRAINT_VALUES,
            ...values,
            id: tempConstraintId,
            name: values.name,
            _metadata: { isOptimistic: true },
          } satisfies QueryListItem<StorageConstraint>,
        ];
      });

      // Await navigation prevents `onError`/`onSuccess` to be called before navigation is done,
      // causing `isRouterMatchTempConstraint()` to not work as expected
      await router.navigate({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId",
        params: { ...params, constraintId: tempConstraintId },
      });
    },
    onError: (error, variables) => {
      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.filter((constraint) => constraint.id !== tempConstraintId);
      });

      enqueueErrorSnackbar(
        t("study.modeling.storages.additionalConstraints.create.error", {
          name: variables.values.name,
        }),
        error,
      );

      if (isRouterMatchTempConstraint()) {
        router.navigate({ to: "..", replace: true });
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
          params: { ...params, constraintId: newConstraint.id },
          replace: true,
        });
      }
    },
  });

  return mutation;
}

export default useCreateStorageConstraint;
