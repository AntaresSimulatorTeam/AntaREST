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

import { Typography, Grid } from "@mui/material";
import type { FieldArrayWithId } from "react-hook-form";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import { useFormContextPlus } from "../../../../../../../common/Form";
import type { AllocationFormFields } from "./utils";
import { validateNumber } from "@/utils/validation/number";

interface Props {
  field: FieldArrayWithId<AllocationFormFields, "allocation">;
  index: number;
  label: string;
}

function AllocationField({ field, index, label }: Props) {
  const { control } = useFormContextPlus<AllocationFormFields>();

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
          name={`allocation.${index}.coefficient` as const}
          control={control}
          rules={{ validate: validateNumber({ min: 0 }) }}
        />
      </Grid>
    </>
  );
}

export default AllocationField;
