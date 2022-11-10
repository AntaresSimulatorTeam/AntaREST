import { Box } from "@mui/material";
import * as R from "ramda";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../../common/types";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../common/Form";
import {
  LINK_TYPE_OPTIONS,
  OptimizationFormFields,
  SIMPLEX_OPTIMIZATION_RANGE_OPTIONS,
  TRANSMISSION_CAPACITIES_OPTIONS,
  UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS,
} from "./utils";

interface Props {
  study: StudyMetadata;
}

function Fields(props: Props) {
  const { study } = props;
  const { t } = useTranslation();
  const { control } = useFormContextPlus<OptimizationFormFields>();
  const isVer830OrAbove = Number(study.version) >= 830;

  return (
    <Box>
      <Fieldset legend={t("study.configuration.optimization.optimization")}>
        <SwitchFE
          label={t("study.configuration.optimization.bindingConstraints")}
          name="bindingConstraints"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.hurdleCosts")}
          name="hurdleCosts"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.optimization.transmissionCapacities")}
          options={TRANSMISSION_CAPACITIES_OPTIONS}
          name="transmissionCapacities"
          control={control}
          rules={{
            setValueAs: R.cond([
              [R.equals("true"), R.T],
              [R.equals("false"), R.F],
              [R.T, R.identity],
            ]),
          }}
        />
        <SelectFE
          label={t("study.configuration.optimization.linkType")}
          options={LINK_TYPE_OPTIONS}
          name="linkType"
          control={control}
        />
        <SwitchFE
          label={t(
            "study.configuration.optimization.thermalClustersMinStablePower"
          )}
          name="thermalClustersMinStablePower"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.thermalClustersMinUdTime")}
          name="thermalClustersMinUdTime"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.dayAheadReserve")}
          name="dayAheadReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.primaryReserve")}
          name="primaryReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.strategicReserve")}
          name="strategicReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.spinningReserve")}
          name="spinningReserve"
          control={control}
        />
        <SwitchFE
          label={t("study.configuration.optimization.exportMps")}
          name="exportMps"
          control={control}
        />
        {isVer830OrAbove && (
          <SwitchFE
            label={t("study.configuration.optimization.splitExportedMps")}
            name="splitExportedMps"
            control={control}
          />
        )}
        <SelectFE
          label={t(
            "study.configuration.optimization.unfeasibleProblemBehavior"
          )}
          options={UNFEASIBLE_PROBLEM_BEHAVIOR_OPTIONS}
          name="unfeasibleProblemBehavior"
          control={control}
        />
        <SelectFE
          label={t("study.configuration.optimization.simplexOptimizationRange")}
          options={SIMPLEX_OPTIMIZATION_RANGE_OPTIONS}
          name="simplexOptimizationRange"
          control={control}
        />
      </Fieldset>
      {isVer830OrAbove && (
        <Fieldset legend={t("study.configuration.optimization.adequacyPatch")}>
          <SwitchFE
            label={t("study.configuration.optimization.enableAdequacyPatch")}
            name="enableAdequacyPatch"
            control={control}
          />
          <SwitchFE
            label={t(
              "study.configuration.optimization.ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch"
            )}
            name="ntcFromPhysicalAreasOutToPhysicalAreasInAdequacyPatch"
            control={control}
          />
          <SwitchFE
            label={t(
              "study.configuration.optimization.ntcBetweenPhysicalAreasOutAdequacyPatch"
            )}
            name="ntcBetweenPhysicalAreasOutAdequacyPatch"
            control={control}
          />
        </Fieldset>
      )}
    </Box>
  );
}

export default Fields;
