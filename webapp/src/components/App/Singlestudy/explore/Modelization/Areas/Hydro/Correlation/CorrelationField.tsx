/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { Typography, Grid } from "@mui/material";
import { FieldArrayWithId } from "react-hook-form";
import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { CorrelationFormFields } from "./utils";
import { useFormContextPlus } from "../../../../../../../common/Form";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentArea } from "../../../../../../../../redux/selectors";

interface Props {
  field: FieldArrayWithId<CorrelationFormFields, "correlation">;
  index: number;
  label: string;
}

// TODO merge with AllocationField
function CorrelationField({ field, index, label }: Props) {
  const { control } = useFormContextPlus<CorrelationFormFields>();
  const currentArea = useAppSelector(getCurrentArea);
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Grid item xs={4} md={2}>
        <Typography
          sx={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </Typography>
      </Grid>
      <Grid item xs={4} md={2}>
        <NumberFE
          key={field.id}
          label={t("study.modelization.hydro.correlation.coefficient")}
          name={`correlation.${index}.coefficient`}
          size="small"
          control={control}
          rules={{
            min: {
              value: -100,
              message: t("form.field.minValue", { 0: -100 }),
            },
            max: {
              value: 100,
              message: t("form.field.maxValue", { 0: 100 }),
            },
          }}
          disabled={field.areaId === currentArea?.id}
        />
      </Grid>
    </>
  );
}

export default CorrelationField;
