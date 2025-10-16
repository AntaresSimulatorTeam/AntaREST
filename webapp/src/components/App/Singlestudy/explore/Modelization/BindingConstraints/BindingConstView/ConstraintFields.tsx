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
import SelectFE from "@/components/common/fieldEditors/SelectFE";
import { validateString } from "@/utils/validation/string";
import type { StudyMetadata } from "../../../../../../../types/types";
import { useFormContextPlus } from "../../../../../../common/Form";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { type BindingConstraint, OPERATORS, OUTPUT_FILTERS, TIME_STEPS } from "./utils";

interface Props {
  study: StudyMetadata;
  constraintId: string;
}

function Fields({ study }: Props) {
  const { t } = useTranslation();
  const { control } = useFormContextPlus<BindingConstraint>();

  const outputFilterOptions = useMemo(
    () =>
      OUTPUT_FILTERS.map((filter) => ({
        label: t(`global.time.${filter}`),
        value: filter,
      })),
    [t],
  );

  const operatorOptions = useMemo(
    () =>
      OPERATORS.map((operator) => ({
        label: t(`study.modelization.bindingConst.operator.${operator}`),
        value: operator,
      })),
    [t],
  );

  const timeStepOptions = useMemo(
    () =>
      TIME_STEPS.map((timeStep) => ({
        label: t(`global.time.${timeStep}`),
        value: timeStep,
      })),
    [t],
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box sx={{ my: 1, width: 1 }}>
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center" }}>
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
        {Number(study.version) >= 870 && (
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
          options={timeStepOptions}
          control={control}
          sx={{ minWidth: 195 }}
        />
        <SelectFE
          name="operator"
          label={t("study.modelization.bindingConst.operator")}
          variant="outlined"
          options={operatorOptions}
          control={control}
          sx={{ minWidth: 195 }}
        />
      </Box>
      {Number(study.version) >= 830 && (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, width: 1, mt: 2 }}>
          <SelectFE
            name="filterYearByYear"
            label={t("study.outputFilters.filterByYear")}
            variant="outlined"
            options={outputFilterOptions}
            multiple
            control={control}
            sx={{ minWidth: 195 }}
          />
          <SelectFE
            name="filterSynthesis"
            label={t("study.outputFilters.filterSynthesis")}
            variant="outlined"
            options={outputFilterOptions}
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
        </Box>
      )}
    </Box>
  );
}

export default Fields;
