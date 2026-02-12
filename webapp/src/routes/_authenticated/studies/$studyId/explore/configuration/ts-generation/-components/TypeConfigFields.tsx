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

import NumberFE from "@/components/fieldEditors/NumberFE";
import type { TimeSeriesTypeValue } from "@/services/api/studies/timeseries/types";
import { validateNumber } from "@/utils/validation/number";
import { TableCell } from "@mui/material";
import { useFormContext } from "react-hook-form";
import type { TimeSeriesConfigValues } from "../-utils";

interface Props {
  type: TimeSeriesTypeValue;
}

function TypeConfigFields({ type }: Props) {
  const { control } = useFormContext<TimeSeriesConfigValues>();

  return (
    <TableCell align="center">
      <NumberFE
        name={`${type}.number` as const}
        control={control}
        rules={{ validate: validateNumber({ min: 1 }) }}
        sx={{ width: 110 }}
        size="extra-small"
        margin="dense"
      />
    </TableCell>
  );
}

export default TypeConfigFields;
