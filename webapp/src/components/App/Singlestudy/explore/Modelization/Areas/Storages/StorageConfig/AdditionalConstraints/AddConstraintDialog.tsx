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

import FormDialog from "@/components/common/dialogs/FormDialog";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import StringFE from "@/components/common/fieldEditors/StringFE";
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import Fieldset from "@/components/common/Fieldset";
import type { SubmitHandlerPlus } from "@/components/common/Form/types";
import { createAdditionalConstraints } from "@/services/api/studies/areas/storages";
import type {
  AdditionalConstraint,
  AdditionalConstraintCreation,
} from "@/services/api/studies/areas/storages/types";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES, OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "./constants";

interface Props {
  open: boolean;
  onClose: VoidFunction;
  onSave: (createdConstraint: AdditionalConstraint) => void;
  studyId: string;
  areaId: string;
  storageId: string;
  existingNames: string[];
}

function AddConstraintDialog({
  open,
  onClose,
  onSave,
  studyId,
  areaId,
  storageId,
  existingNames,
}: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<AdditionalConstraintCreation>) => {
    return createAdditionalConstraints({
      studyId,
      areaId,
      storageId,
      constraints: [values],
    });
  };

  const handleSubmitSuccessful = (
    _: SubmitHandlerPlus<AdditionalConstraintCreation>,
    submitResult: AdditionalConstraint[],
  ) => {
    onSave(submitResult[0]);
    onClose();
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
      onSubmitSuccessful={handleSubmitSuccessful}
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
            label={t("study.modelization.storages.additionalConstraints.variable")}
            name="variable"
            control={control}
            options={VARIABLE_OPTIONS}
          />
          <SelectFE
            label={t("study.modelization.storages.additionalConstraints.bounds")}
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
