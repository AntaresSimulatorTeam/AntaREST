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

import { useFormContextPlus } from "@/components/common/Form";
import NumberFE from "@/components/common/fieldEditors/NumberFE";
import { TableCell } from "@mui/material";
import type { TimeSeriesConfigValues } from "../utils";
import { validateNumber } from "@/utils/validation/number";
import type { TimeSeriesTypeValue } from "@/services/api/studies/timeseries/types";
import { useWatch } from "react-hook-form";

interface Props {
  type: TimeSeriesTypeValue;
}

function TypeConfigFields({ type }: Props) {
  const { control } = useFormContextPlus<TimeSeriesConfigValues>();

  const isEnable = useWatch({
    name: `${type}.enable`,
    control,
  });

  return (
    <TableCell align="center">
      <NumberFE
        name={`${type}.number` as const}
        control={control}
        size="small"
        disabled={!isEnable}
        rules={{ validate: validateNumber({ min: 1 }) }}
        sx={{ width: 110 }}
      />
    </TableCell>
  );
}

export default TypeConfigFields;
