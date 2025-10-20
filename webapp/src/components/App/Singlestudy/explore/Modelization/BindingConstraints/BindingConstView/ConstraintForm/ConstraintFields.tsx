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

import Fieldset from "@/components/common/Fieldset";
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import { validateString } from "@/utils/validation/string";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../../../types/types";
import { useFormContextPlus } from "../../../../../../../common/Form";
import StringFE from "../../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  type BindingConstraint,
  OPERATOR_OPTIONS,
  OUTPUT_FILTERS_OPTIONS,
  TIME_STEPS_OPTIONS,
} from "../utils";

interface Props {
  study: StudyMetadata;
  constraintId: string;
}

function ConstraintFields({ study }: Props) {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<BindingConstraint>();
  const studyVersion = Number(study.version);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Fieldset>
      <SwitchFE
        name="enabled"
        label={t("study.modelization.bindingConst.enabled")}
        control={control}
        sx={{
          "& .MuiFormControlLabel-root": {
            ml: 0,
          },
        }}
      />
      <StringFE
        disabled
        name="name"
        label={t("global.name")}
        control={control}
        rules={{ validate: (v) => validateString(v) }}
      />
      {studyVersion >= 870 && (
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
      <SelectFE
        name="timeStep"
        label={t("study.modelization.bindingConst.type")}
        variant="outlined"
        options={TIME_STEPS_OPTIONS}
        control={control}
        sx={{ minWidth: 195 }}
      />
      <SelectFE
        name="operator"
        label={t("study.modelization.bindingConst.operator")}
        variant="outlined"
        options={OPERATOR_OPTIONS}
        control={control}
        sx={{ minWidth: 195 }}
      />
      {studyVersion >= 830 && (
        <>
          <SelectFE
            name="filterYearByYear"
            label={t("study.outputFilters.filterByYear")}
            variant="outlined"
            options={OUTPUT_FILTERS_OPTIONS}
            multiple
            control={control}
            sx={{ minWidth: 195 }}
          />
          <SelectFE
            name="filterSynthesis"
            label={t("study.outputFilters.filterSynthesis")}
            variant="outlined"
            options={OUTPUT_FILTERS_OPTIONS}
            multiple
            control={control}
            sx={{ minWidth: 195 }}
          />
          <StringFE
            name="comments"
            label={t("study.modelization.bindingConst.comments")}
            control={control}
            required={false}
            sx={{ minWidth: 195 }}
          />
        </>
      )}
    </Fieldset>
  );
}

export default ConstraintFields;
