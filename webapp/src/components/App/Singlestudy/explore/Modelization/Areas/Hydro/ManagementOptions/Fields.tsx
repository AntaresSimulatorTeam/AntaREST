import { Box } from "@mui/system";
import NumberFE from "../../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../../common/Form";
import { INITIALIZE_RESERVOIR_DATE_OPTIONS, HydroFormFields } from "./utils";

function Fields() {
  const { control, watch } = useFormContextPlus<HydroFormFields>();
  const [
    reservoirDisabled,
    waterValuesDisabled,
    heuristicDisabled,
    leeWayDisabled,
  ] = watch(["reservoir", "useWater", "useHeuristic", "useLeeway"]);

  return (
    <Box sx={{ px: 3 }}>
      <Fieldset legend="General parameters">
        <SwitchFE
          name="followLoad"
          label="Follow load modulations"
          control={control}
          sx={{ alignSelf: "center" }}
        />
        <NumberFE
          name="interDailyBreakdown"
          label="Inter Daily Breakdown"
          control={control}
        />
        <NumberFE
          name="intraDailyModulation"
          label="Intra-daily modulation"
          control={control}
        />
      </Fieldset>
      <Fieldset legend="Reservoir management">
        <Box>
          <SwitchFE
            name="reservoir"
            label="Reservoir management"
            control={control}
          />
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
        </Box>
        <Box
          sx={{
            alignItems: "center",
          }}
        >
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
          />
        </Box>
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
            (!waterValuesDisabled || !leeWayDisabled) &&
            (!waterValuesDisabled || heuristicDisabled)
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
    </Box>
  );
}

export default Fields;
