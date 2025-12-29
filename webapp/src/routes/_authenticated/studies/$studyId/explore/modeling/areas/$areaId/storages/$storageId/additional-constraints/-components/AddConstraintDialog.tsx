/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import FormDialog from "@/components/dialogs/FormDialog";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useSafeMemo from "@/hooks/useSafeMemo";
import { storageMutations, storageQueries } from "@/queries/storages";
import type { StorageConstraintCreation } from "@/services/api/studies/areas/storages/types";
import { getNames } from "@/services/utils";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useMutation, useSuspenseQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES, OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "../-constants";

interface Props {
  onCancel: VoidFunction;
}

function AddConstraintDialog({ onCancel }: Props) {
  const { t } = useTranslation();
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const router = useRouter();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const tempConstraintId = useSafeMemo(() => crypto.randomUUID(), []);
  const { studyId, areaId, storageId } = params;
  const queryOptions = storageQueries.constraintList(studyId, areaId, storageId);
  const { queryKey } = queryOptions;

  const { data: existingNames } = useSuspenseQuery({
    ...queryOptions,
    select: getNames,
  });

  const isRouterMatchConstraint = (constraintId: string) => {
    return router.state.matches.some(
      (m) =>
        m.routeId ===
          "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId/" &&
        m.params.constraintId === constraintId,
    );
  };

  const { mutate } = useMutation({
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

      router.navigate({
        to: "/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId",
        params: { ...params, constraintId: tempConstraintId },
      });

      return { prevConstraints };
    },
    onError: (error, variables, onMutateResult, context) => {
      const { prevConstraints } = onMutateResult || {};

      context.client.setQueryData(queryKey, prevConstraints);

      enqueueErrorSnackbar("Not adding", error);

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

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<StorageConstraintCreation>) => {
    mutate({ ...params, values });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open
      title={t("study.modeling.storages.additionalConstraints.add")}
      titleIcon={AddCircleIcon}
      onCancel={onCancel}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onCancel}
      config={{ defaultValues: DEFAULT_CONSTRAINT_VALUES }}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            label={t("global.name")}
            name="name"
            control={control}
            rules={{ validate: validateString({ existingValues: existingNames }) }}
          />
          <SelectFE
            label={t("study.modeling.storages.additionalConstraints.variable")}
            name="variable"
            control={control}
            options={VARIABLE_OPTIONS}
          />
          <SelectFE
            label={t("study.modeling.storages.additionalConstraints.bounds")}
            name="operator"
            control={control}
            options={OPERATOR_OPTIONS}
          />
          <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default AddConstraintDialog;
