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
import { useTranslation } from "react-i18next";
import Fieldset from "@/components/common/Fieldset";
import Form from "@/components/common/Form";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import {
  getAdditionalConstraint,
  updateAdditionalConstraints,
} from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import { CONSTRAINT_OPERATORS, CONSTRAINT_VARIABLES } from "./constants";
import { validateString } from "@/utils/validation/string";

interface Props {
  studyId: string;
  areaId: string;
  storageId: string;
  constraint: AdditionalConstraint;
  onUpdate: () => void;
}

function ConstraintDetails({ studyId, areaId, storageId, constraint, onUpdate }: Props) {
  const { t } = useTranslation();

  const variableOptions = CONSTRAINT_VARIABLES.map((option) => ({
    value: option.value,
    label: t(option.label),
  }));

  const operatorOptions = CONSTRAINT_OPERATORS.map((option) => ({
    value: option.value,
    label: option.label,
  }));

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

    return updateAdditionalConstraints({
      studyId,
      areaId,
      storageId,
      constraints: {
        [constraint.id]: updatedConstraint,
      },
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ height: 1, display: "flex", flexDirection: "column" }}>
      <Form
        key={`${studyId}-${areaId}-${storageId}-${constraint.id}`}
        onSubmit={handleSubmit}
        // TODO: replace the reload()
        onSubmitSuccessful={onUpdate}
        config={{ defaultValues: getDefaultValues }}
        enableUndoRedo
      >
        {({ control }) => (
          <Box sx={{ mb: 2 }}>
            <Fieldset legend={t("study.modelization.storages.additionalConstraints.properties")}>
              <StringFE
                label={t("global.name")}
                name="id"
                control={control}
                size="small"
                rules={{
                  validate: (v) => validateString(v),
                }}
              />

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
