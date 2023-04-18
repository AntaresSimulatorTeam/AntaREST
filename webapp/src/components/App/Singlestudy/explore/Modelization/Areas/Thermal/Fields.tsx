import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import {
  CLUSTER_GROUP_OPTIONS,
  ThermalFormFields,
  TS_GENERATION_OPTIONS,
  TS_LAW_OPTIONS,
} from "./utils";

function Fields() {
  const [t] = useTranslation();
  const { control } = useFormContextPlus<ThermalFormFields>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Fieldset legend={t("global.general")}>
        <StringFE
          label={t("global.name")}
          name="name"
          control={control}
          disabled
        />
        <SelectFE
          label={t("study.modelization.clusters.group")}
          name="group"
          control={control}
          options={CLUSTER_GROUP_OPTIONS}
          sx={{
            alignSelf: "center",
          }}
        />
      </Fieldset>
      <Fieldset legend={t("study.modelization.clusters.operatingParameters")}>
        <SwitchFE
          label={t("study.modelization.clusters.enabled")}
          name="enabled"
          control={control}
          sx={{
            alignItems: "center",
            alignSelf: "center",
          }}
        />
        <SwitchFE
          label={t("study.modelization.clusters.mustRun")}
          name="mustRun"
          control={control}
          sx={{
            alignItems: "center",
            alignSelf: "center",
          }}
        />
        <NumberFE
          label={t("study.modelization.clusters.unitcount")}
          name="unitCount"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.nominalCapacity")}
          name="nominalCapacity"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.minStablePower")}
          name="minStablePower"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.spinning")}
          name="spinning"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.minUpTime")}
          name="minUpTime"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.minDownTime")}
          name="minDownTime"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.co2")}
          name="co2"
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.modelization.clusters.operatingCosts")}>
        <NumberFE
          label={t("study.modelization.clusters.marginalCost")}
          name="marginalCost"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.fixedCost")}
          name="fixedCost"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.startupCost")}
          name="startupCost"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.marketBidCost")}
          name="marketBidCost"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.spreadCost")}
          name="spreadCost"
          control={control}
        />
      </Fieldset>
      <Fieldset legend={t("study.modelization.clusters.timeSeriesGen")}>
        <SelectFE
          label={t("study.modelization.clusters.genTs")}
          name="genTs"
          control={control}
          options={TS_GENERATION_OPTIONS}
          sx={{
            alignSelf: "center",
          }}
        />
        <NumberFE
          label={t("study.modelization.clusters.volatilityForced")}
          name="volatilityForced"
          control={control}
        />
        <NumberFE
          label={t("study.modelization.clusters.volatilityPlanned")}
          name="volatilityPlanned"
          control={control}
        />
        <SelectFE
          label={t("study.modelization.clusters.lawForced")}
          name="lawForced"
          control={control}
          options={TS_LAW_OPTIONS}
          sx={{
            alignSelf: "center",
          }}
        />
        <SelectFE
          label={t("study.modelization.clusters.lawPlanned")}
          name="lawPlanned"
          control={control}
          options={TS_LAW_OPTIONS}
          sx={{
            alignSelf: "center",
          }}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
