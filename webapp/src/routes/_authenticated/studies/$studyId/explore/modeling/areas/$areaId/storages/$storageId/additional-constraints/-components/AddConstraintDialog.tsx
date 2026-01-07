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
import { storageQueries } from "@/queries/storages";
import type { StorageConstraintCreation } from "@/services/api/studies/areas/storages/types";
import { getNames } from "@/services/utils";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { DEFAULT_CONSTRAINT_VALUES, OPERATOR_OPTIONS, VARIABLE_OPTIONS } from "../-constants";
import useCreateStorageConstraint from "../-hooks/useCreateStorageConstraint";

interface Props {
  onCancel: VoidFunction;
}

function AddConstraintDialog({ onCancel }: Props) {
  const { t } = useTranslation();
  const params = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });

  const { studyId, areaId, storageId } = params;

  const { data: existingNames } = useSuspenseQuery({
    ...storageQueries.constraintList(studyId, areaId, storageId),
    select: getNames,
  });

  const createConstraint = useCreateStorageConstraint();

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<StorageConstraintCreation>) => {
    createConstraint.mutate({ ...params, values });
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
