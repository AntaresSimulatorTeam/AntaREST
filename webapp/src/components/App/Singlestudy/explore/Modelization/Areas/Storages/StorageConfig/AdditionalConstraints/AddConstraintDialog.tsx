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

import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import FormDialog from "@/components/common/dialogs/FormDialog";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import { createAdditionalConstraints } from "@/services/api/studies/areas/storages";
import type { AdditionalConstraint } from "@/services/api/studies/areas/storages/types";
import { validateString } from "@/utils/validation/string";
import { CONSTRAINT_OPERATORS, CONSTRAINT_VARIABLES, DEFAULT_CONSTRAINT_VALUES } from "./constants";

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  studyId: string;
  areaId: string;
  storageId: string;
}

interface FormValues {
  name: string;
  variable: AdditionalConstraint["variable"];
  bounds: AdditionalConstraint["operator"];
  enabled: boolean;
}

function AddConstraintDialog({ open, onClose, onSave, studyId, areaId, storageId }: Props) {
  const { t } = useTranslation();

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

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ values }: SubmitHandlerPlus<FormValues>) => {
    const { name, variable, bounds, enabled } = values;

    await createAdditionalConstraints({
      studyId,
      areaId,
      storageId,
      constraints: [
        {
          name,
          variable,
          operator: bounds,
          enabled,
          occurrences: [],
        },
      ],
    });

    onSave();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("study.modelization.storages.additionalConstraints.add")}
      titleIcon={AddCircleIcon}
      open={open}
      onCancel={onClose}
      onSubmit={handleSubmit}
      maxWidth="sm"
      config={{
        defaultValues: DEFAULT_CONSTRAINT_VALUES,
      }}
    >
      {({ control }) => (
        <>
          <Fieldset fullFieldWidth>
            <StringFE
              label={t("global.name")}
              name="name"
              control={control}
              fullWidth
              required
              rules={{
                validate: (v) => validateString(v),
              }}
              sx={{ m: 0 }}
            />

            <SelectFE
              label={t("study.modelization.storages.additionalConstraints.variable")}
              name="variable"
              control={control}
              options={variableOptions}
              required
            />

            <SelectFE
              label={t("study.modelization.storages.additionalConstraints.bounds")}
              name="bounds"
              control={control}
              options={operatorOptions}
              required
            />

            <SwitchFE label={t("global.enabled")} name="enabled" control={control} />
          </Fieldset>
        </>
      )}
    </FormDialog>
  );
}

export default AddConstraintDialog;
