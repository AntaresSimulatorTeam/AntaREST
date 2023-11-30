import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import {
  RENEWABLE_GROUPS,
  RenewableCluster,
  TS_INTERPRETATION_OPTIONS,
} from "./utils";

function Fields() {
  const [t] = useTranslation();
  const { control } = useFormContextPlus<RenewableCluster>();

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
          options={RENEWABLE_GROUPS}
          sx={{
            alignSelf: "center",
          }}
        />
        <SelectFE
          label={t("study.modelization.clusters.tsInterpretation")}
          name="tsInterpretation"
          control={control}
          options={TS_INTERPRETATION_OPTIONS}
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
        <NumberFE
          label={t("study.modelization.clusters.unitcount")}
          name="unitCount"
          control={control}
          rules={{
            min: {
              value: 1,
              message: t("form.field.minValue", { 0: 1 }),
            },
            setValueAs: Math.floor,
          }}
        />
        <NumberFE
          label={t("study.modelization.clusters.nominalCapacity")}
          name="nominalCapacity"
          control={control}
          rules={{
            min: {
              value: 0,
              message: t("form.field.minValue", { 0: 0 }),
            },
          }}
        />
      </Fieldset>
    </>
  );
}

export default Fields;
