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
import { useTranslation } from "react-i18next";
import FormDialog from "@/components/common/dialogs/FormDialog";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import type { StudyMetadata } from "@/types/types";
import { validateString } from "@/utils/validation/string";
import { type AdditionalConstraint, createAdditionalConstraint } from "./utils";

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: () => void;
  study: StudyMetadata;
  areaId: string;
  storageId: string;
}

interface FormValues {
  name: string;
  variable: AdditionalConstraint["variable"];
  bounds: AdditionalConstraint["operator"];
  enabled: boolean;
}

function AddConstraintDialog({ open, onClose, onSave, study, areaId, storageId }: Props) {
  const { t } = useTranslation();

  const VARIABLE_OPTIONS = [
    { value: "withdrawal", label: t("study.modelization.storages.additionalConstraints.charge") },
    { value: "injection", label: t("study.modelization.storages.additionalConstraints.discharge") },
    { value: "netting", label: t("study.modelization.storages.additionalConstraints.level") },
  ];

  const BOUNDS_OPTIONS = [
    { value: "less", label: "<" },
    { value: "equal", label: "=" },
    { value: "greater", label: ">" },
  ];

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({ values }: SubmitHandlerPlus<FormValues>) => {
    await createAdditionalConstraint(study.id, areaId, storageId, {
      name: values.name.trim(),
      variable: values.variable,
      bounds: values.bounds,
      enabled: values.enabled,
      hours: [],
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
        defaultValues: {
          name: "",
          variable: "withdrawal",
          bounds: "less",
          enabled: true,
        },
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
              options={VARIABLE_OPTIONS}
              required
            />

            <SelectFE
              label={t("study.modelization.storages.additionalConstraints.bounds")}
              name="bounds"
              control={control}
              options={BOUNDS_OPTIONS}
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
