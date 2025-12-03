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
import SwitchFE from "@/components/common/fieldEditors/SwitchFE";
import { TimeSeriesType } from "@/services/api/studies/timeseries/constants";
import type { TimeSeriesTypeValue } from "@/services/api/studies/timeseries/types";
import { TableCell } from "@mui/material";
import { useWatch } from "react-hook-form";
import type { TimeSeriesConfigValues } from "../utils";

interface Props {
  type: TimeSeriesTypeValue;
}

function OutageDetailsField({ type }: Props) {
    const { control } = useFormContextPlus<TimeSeriesConfigValues>();
  
    const isEnabled = useWatch({
      name: `${type}.enabled`,
      control,
    });
  
    if (type !== TimeSeriesType.Thermal) {
      return <TableCell />;
    }
  
    return (
      <TableCell align="center">
        <SwitchFE
          name={`${type}.outage_details_thermal` as const}  // ← Use snake_case
          control={control}
          disabled={!isEnabled}
          size="small"
        />
      </TableCell>
    );
  }

export default OutageDetailsField;