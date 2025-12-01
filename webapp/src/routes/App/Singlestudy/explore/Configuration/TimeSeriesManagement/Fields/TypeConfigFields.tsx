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
import type { TimeSeriesTypeValue } from "@/services/api/studies/timeseries/types";
import { validateNumber } from "@/utils/validation/number";
import { TableCell } from "@mui/material";
import { useWatch } from "react-hook-form";
import type { TimeSeriesConfigValues } from "../utils";

interface Props {
  type: TimeSeriesTypeValue;
}

function TypeConfigFields({ type }: Props) {
  const { control } = useFormContextPlus<TimeSeriesConfigValues>();

  const isEnabled = useWatch({
    name: `${type}.enabled`,
    control,
  });

  return (
    <TableCell align="center">
      <NumberFE
        name={`${type}.number` as const}
        control={control}
        disabled={!isEnabled}
        rules={{ validate: validateNumber({ min: 1 }) }}
        sx={{ width: 110 }}
        size="extra-small"
        margin="dense"
      />
    </TableCell>
  );
}

export default TypeConfigFields;
