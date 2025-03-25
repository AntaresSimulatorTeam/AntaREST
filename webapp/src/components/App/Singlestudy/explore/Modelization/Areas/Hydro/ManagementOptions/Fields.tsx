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

import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { INITIALIZE_RESERVOIR_DATE_OPTIONS, type HydroFormFields } from "./utils";
import type { StudyMetadata } from "@/types/types";

interface Props {
  study: StudyMetadata;
}

function Fields({ study }: Props) {
  const { control, watch } = useFormContextPlus<HydroFormFields>();
  const [reservoirDisabled, waterValuesDisabled, heuristicDisabled, leeWayDisabled] = watch([
    "reservoir",
    "useWater",
    "useHeuristic",
    "useLeeway",
  ]);
  const studyVersion = Number(study.version);

  return (
    <>
      <Fieldset legend="General parameters">
        <SwitchFE
          name="followLoad"
          label="Follow load modulations"
          control={control}
          sx={{ alignSelf: "center" }}
        />
        <NumberFE name="interDailyBreakdown" label="Inter Daily Breakdown" control={control} />
        <NumberFE name="intraDailyModulation" label="Intra-daily modulation" control={control} />
      </Fieldset>
      <Fieldset legend="Reservoir management">
        <SwitchFE name="reservoir" label="Reservoir management" control={control} />
        <SwitchFE
          name="hardBounds"
          label="Hard bounds on rules curves"
          control={control}
          disabled={!reservoirDisabled}
        />
        <SwitchFE
          name="useHeuristic"
          label="Use heuristic target"
          control={control}
          disabled={!reservoirDisabled}
        />
        <NumberFE
          name="reservoirCapacity"
          label="Reservoir capacity (MWh)"
          control={control}
          disabled={!reservoirDisabled}
        />
        <NumberFE
          name="interMonthlyBreakdown"
          label="Inter-monthly breakdown"
          control={control}
          disabled={!reservoirDisabled}
        />
        <NumberFE
          name="pumpingEfficiency"
          label="Pumping Efficiency Ratio"
          control={control}
          disabled={!reservoirDisabled}
        />
        <SelectFE
          name="initializeReservoirDate"
          options={INITIALIZE_RESERVOIR_DATE_OPTIONS}
          label="Initialize reservoir level on"
          control={control}
          disabled={!reservoirDisabled}
          sx={{ alignSelf: "center" }}
        />
        {studyVersion >= 920 && (
          <NumberFE
            name="overflowSpilledCostDifference"
            label="Overflow Spilled Cost Difference"
            control={control}
            disabled={!reservoirDisabled}
          />
        )}
      </Fieldset>
      <Fieldset legend="Water values">
        <SwitchFE name="useWater" label="Use water values" control={control} />
      </Fieldset>
      <Fieldset legend="Mixed management">
        <SwitchFE
          name="useLeeway"
          label="Use leeway"
          control={control}
          disabled={!waterValuesDisabled || !heuristicDisabled}
        />
        <SwitchFE
          name="powerToLevel"
          label="Power to level modulations"
          control={control}
          disabled={
            (!waterValuesDisabled || !leeWayDisabled) && (!waterValuesDisabled || heuristicDisabled)
          }
        />
        <NumberFE
          name="leewayLow"
          label="Leeway low bound"
          control={control}
          disabled={!waterValuesDisabled || !leeWayDisabled}
        />
        <NumberFE
          name="leewayUp"
          label="Leeway upper bound"
          control={control}
          disabled={!waterValuesDisabled || !leeWayDisabled}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
