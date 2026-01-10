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

import { useFormContextPlus } from "@/components/Form";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import SwitchFE from "@/components/fieldEditors/SwitchFE";
import { validateString } from "@/utils/validation/string";
import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import semver from "semver";
import {
  type BindingConstraint,
  OPERATOR_OPTIONS,
  OUTPUT_FILTERS_OPTIONS,
  TIME_STEPS_OPTIONS,
} from "../../-utils";
import type { StudyMetadata } from "../../../../../../../../../types/types";

interface Props {
  study: StudyMetadata;
  constraintId: string;
}

function ConstraintFields({ study }: Props) {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<BindingConstraint>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ my: 1, width: 1 }}>
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center" }}>
        <SwitchFE
          name="enabled"
          label={t("study.modeling.bindingConst.enabled")}
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
        <SelectFE
          name="timeStep"
          label={t("study.modeling.bindingConst.type")}
          variant="outlined"
          options={TIME_STEPS_OPTIONS}
          control={control}
          sx={{ minWidth: 195 }}
        />
        <SelectFE
          name="operator"
          label={t("study.modeling.bindingConst.operator")}
          variant="outlined"
          options={OPERATOR_OPTIONS}
          control={control}
          sx={{ minWidth: 100 }}
        />
        <Box sx={{ display: "flex", gap: 1, mt: 1, width: 1 }}>
          {semver.gte(study.version, "8.3.0") && (
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
                label={t("study.modeling.bindingConst.comments")}
                control={control}
                required={false}
                sx={{ minWidth: 195 }}
              />
            </>
          )}
        </Box>
      </Box>
    </Box>
  );
}

export default ConstraintFields;
