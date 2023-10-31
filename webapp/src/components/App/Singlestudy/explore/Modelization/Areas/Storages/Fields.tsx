import { useTranslation } from "react-i18next";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import { STORAGE_GROUP_OPTIONS, Storage } from "./utils";

function Fields() {
  const [t] = useTranslation();
  const { control } = useFormContextPlus<Storage>();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
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
        options={STORAGE_GROUP_OPTIONS}
        sx={{
          alignSelf: "center",
        }}
      />
      <NumberFE
        label="Injection Nominal Capacity"
        name="injectionNominalCapacity"
        control={control}
      />
      <NumberFE
        label="Withdrawal Capacity"
        name="withdrawalNominalCapacity"
        control={control}
      />
      <NumberFE
        label="Reservoir Capacity"
        name="reservoirCapacity"
        control={control}
      />
      <NumberFE label="Efficiency" name="efficiency" control={control} />
      <NumberFE label="Initial Level" name="initialLevel" control={control} />
      <SwitchFE
        label="Initial Level Optim"
        name="initialLevelOptim"
        control={control}
        sx={{
          alignItems: "center",
          alignSelf: "center",
        }}
      />
    </Fieldset>
  );
}

export default Fields;
