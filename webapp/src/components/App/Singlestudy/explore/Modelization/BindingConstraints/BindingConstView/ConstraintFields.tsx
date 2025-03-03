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

import { type BindingConstraint, OPERATORS, OUTPUT_FILTERS, TIME_STEPS } from "./utils";

import Fieldset from "../../../../../../common/Fieldset";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import type { StudyMetadata } from "../../../../../../../types/types";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { useFormContextPlus } from "../../../../../../common/Form";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Button } from "@mui/material";
import DatasetIcon from "@mui/icons-material/Dataset";
import { validateString } from "@/utils/validation/string";
import ConstraintMatrix from "./Matrix";

interface Props {
  study: StudyMetadata;
  constraintId: string;
}

function Fields({ study, constraintId }: Props) {
  const { t } = useTranslation();
  const { control, getValues } = useFormContextPlus<BindingConstraint>();
  const [matrixDialogOpen, setMatrixDialogOpen] = useState(false);
  const currentOperator = getValues("operator");

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
    <>
      <Fieldset legend={t("global.general")} fieldWidth={280} sx={{ py: 1, flexWrap: "wrap" }}>
        <SwitchFE
          name="enabled"
          label={t("study.modelization.bindingConst.enabled")}
          control={control}
        />
        <StringFE
          disabled
          name="name"
          label={t("global.name")}
          control={control}
          rules={{ validate: (v) => validateString(v) }}
          sx={{ m: 0, minWidth: 280 }} // TODO: Remove margin reset when updating MUI Theme
        />
        {Number(study.version) >= 870 && (
          <StringFE
            name="group"
            label={t("global.group")}
            control={control}
            rules={{
              validate: (v) =>
                validateString(v, {
                  maxLength: 20,
                  specialChars: "-",
                }),
            }}
            sx={{ m: 0, minWidth: 280 }} // TODO: Remove margin reset when updating MUI Theme
          />
        )}
        <SelectFE
          name="timeStep"
          label={t("study.modelization.bindingConst.type")}
          variant="outlined"
          options={timeStepOptions}
          control={control}
          sx={{ maxWidth: 180 }}
        />
        <SelectFE
          name="operator"
          label={t("study.modelization.bindingConst.operator")}
          variant="outlined"
          options={operatorOptions}
          control={control}
          sx={{ maxWidth: 150 }}
        />
        {Number(study.version) >= 830 && (
          <Box sx={{ display: "flex", gap: 2, width: 1 }}>
            <SelectFE
              name="filterYearByYear"
              label={t("study.outputFilters.filterByYear")}
              variant="outlined"
              options={outputFilterOptions}
              multiple
              control={control}
            />
            <SelectFE
              name="filterSynthesis"
              label={t("study.outputFilters.filterSynthesis")}
              variant="outlined"
              options={outputFilterOptions}
              multiple
              control={control}
            />
            <StringFE
              name="comments"
              label={t("study.modelization.bindingConst.comments")}
              control={control}
              required={false}
              sx={{ m: 0, minWidth: 280 }} // TODO: Remove margin reset when updating MUI Theme
            />
          </Box>
        )}
      </Fieldset>
      <Box>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<DatasetIcon />}
          onClick={() => setMatrixDialogOpen(true)}
          sx={{ mt: 2 }}
        >
          {t("study.modelization.bindingConst.timeSeries")}
        </Button>
      </Box>

      {matrixDialogOpen && (
        <ConstraintMatrix
          study={study}
          constraintId={constraintId}
          operator={currentOperator}
          open={matrixDialogOpen}
          onClose={() => setMatrixDialogOpen(false)}
        />
      )}
    </>
  );
}

export default Fields;
