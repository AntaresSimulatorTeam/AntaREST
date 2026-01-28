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

import FormDialog from "@/components/dialogs/FormDialog";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { bindingConstraintQueries } from "@/queries/bindingConstraints/queries";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import type { BindingConstraintCreationDTO } from "@/services/api/studies/bindingConstraints/type";
import { getNames } from "@/services/utils";
import { validateString } from "@/utils/validation/string";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import { useSuspenseQuery } from "@tanstack/react-query";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import semver from "semver";
import useCreateBindingConstraint from "../-hooks/useCreateBindingConstraint";
import { DEFAULT_CONSTRAINT_VALUES, OPERATOR_OPTIONS, TIME_STEPS_OPTIONS } from "../-utils";

interface Props {
  onCancel: VoidFunction;
}

const defaultValues = R.pick(
  ["enabled", "name", "group", "comments", "timeStep", "operator"],
  DEFAULT_CONSTRAINT_VALUES,
);

function AddConstraintDialog({ onCancel }: Props) {
  const study = useStudy();
  const { t } = useTranslation();
  const createConstraint = useCreateBindingConstraint();

  const { data: existingNames } = useSuspenseQuery({
    ...bindingConstraintQueries.list(study.id),
    select: getNames,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = ({ values }: SubmitHandlerPlus<BindingConstraintCreationDTO>) => {
    createConstraint.mutate({ studyId: study.id, values });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open
      title={t("study.modeling.bindingConst.newBindingConst")}
      titleIcon={AddCircleIcon}
      config={{ defaultValues }}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onCancel}
      onCancel={onCancel}
    >
      {({ control }) => (
        <Fieldset fullFieldWidth>
          <SwitchFE
            name="enabled"
            label={t("study.modeling.bindingConst.enabled")}
            control={control}
          />
          <StringFE
            name="name"
            label={t("global.name")}
            control={control}
            rules={{
              validate: (v) =>
                validateString(v, {
                  existingValues: existingNames,
                  specialChars: "@&_-()",
                }),
            }}
          />
          {semver.gte(study.version, "8.7.0") && (
            <StringFE
              name="group"
              label={t("global.group")}
              control={control}
              rules={{
                validate: (v) => {
                  if (typeof v === "string") {
                    return validateString(v, {
                      maxLength: 20,
                      specialChars: "-",
                    });
                  }
                },
              }}
            />
          )}
          <StringFE
            name="comments"
            label={t("study.modeling.bindingConst.comments")}
            control={control}
          />
          <SelectFE
            name="timeStep"
            label={t("study.modeling.bindingConst.type")}
            variant="outlined"
            options={TIME_STEPS_OPTIONS}
            control={control}
          />
          <SelectFE
            name="operator"
            label={t("study.modeling.bindingConst.operator")}
            variant="outlined"
            options={OPERATOR_OPTIONS}
            control={control}
          />
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default AddConstraintDialog;
