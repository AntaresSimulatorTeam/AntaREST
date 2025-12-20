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
import useArea from "@/routes/-shared/hook/useArea";
import useStudy from "@/routes/-shared/hook/useStudy";
import { createAdditionalConstraint } from "@/services/api/studies/areas/storages";
import type {
  AdditionalConstraint,
  AdditionalConstraintCreation,
} from "@/services/api/studies/areas/storages/types";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES, OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "../-constants";

interface Props {
  onCancel: VoidFunction;
  existingNames: string[];
}

function AddConstraintDialog({ onCancel, existingNames }: Props) {
  const study = useStudy();
  const area = useArea();
  const { storageId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<AdditionalConstraintCreation>) => {
    return createAdditionalConstraint({
      studyId: study.id,
      areaId: area.id,
      storageId,
      values,
    });
  };

  const handleSumitSuccessful = (
    data: SubmitHandlerPlus<AdditionalConstraintCreation>,
    createdConstraint: AdditionalConstraint,
  ) => {
    // navigate({
    //   to: "/studies/$studyId/explore/tablemode/$tableModeId",
    //   params: { studyId: study.id, tableModeId: values.name },
    //   replace: isUpdateDialog ? true : false,
    // });

    onCancel();
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
      onSubmitSuccessful={handleSumitSuccessful}
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
