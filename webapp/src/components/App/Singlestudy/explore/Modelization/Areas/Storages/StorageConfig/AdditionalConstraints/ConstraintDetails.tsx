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

import { Box } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import Fieldset from "@/components/common/Fieldset";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import {
  getAdditionalConstraint,
  updateAdditionalConstraints,
} from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import { toError } from "@/utils/fnUtils";
import { CONSTRAINT_OPERATORS, CONSTRAINT_VARIABLES } from "./constants";

interface Props {
  studyId: string;
  areaId: string;
  storageId: string;
  constraint: AdditionalConstraint;
  onUpdate: () => void;
}

function ConstraintDetails({ studyId, areaId, storageId, constraint, onUpdate }: Props) {
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const variableOptions = useMemo(
    () =>
      CONSTRAINT_VARIABLES.map((option) => ({
        value: option.value,
        label: t(option.label),
      })),
    [t],
  );

  const operatorOptions = useMemo(
    () =>
      CONSTRAINT_OPERATORS.map((option) => ({
        value: option.value,
        label: option.label,
      })),
    [],
  );

  const getDefaultValues = () => {
    return getAdditionalConstraint({
      studyId,
      areaId,
      storageId,
      constraintId: constraint.id,
    });
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ values }: SubmitHandlerPlus<AdditionalConstraint>) => {
    const { id, name, ...updatedConstraint } = values;

    try {
      await updateAdditionalConstraints({
        studyId,
        areaId,
        storageId,
        constraints: {
          [constraint.id]: updatedConstraint,
        },
      });

      onUpdate();
    } catch (error) {
      enqueueErrorSnackbar(t("global.error.create"), toError(error));
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ height: 1, display: "flex", flexDirection: "column" }}>
      <Form
        key={`${studyId}-${areaId}-${storageId}-${constraint.id}`}
        config={{ defaultValues: getDefaultValues }}
        onSubmit={handleSubmit}
        enableUndoRedo
      >
        {({ control }) => (
          <Box sx={{ mb: 2 }}>
            <Fieldset legend={t("study.modelization.storages.additionalConstraints.properties")}>
              <StringFE label={t("global.name")} name="id" control={control} size="small" />

              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.variable")}
                name="variable"
                control={control}
                options={variableOptions}
                size="small"
              />

              <SelectFE
                label={t("study.modelization.storages.additionalConstraints.bounds")}
                name="operator"
                control={control}
                options={operatorOptions}
                size="small"
              />

              <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
            </Fieldset>
          </Box>
        )}
      </Form>
    </Box>
  );
}

export default ConstraintDetails;
