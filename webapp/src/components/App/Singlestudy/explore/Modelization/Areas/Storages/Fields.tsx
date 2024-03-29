import { useTranslation } from "react-i18next";
import { Box, Tooltip } from "@mui/material";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import Fieldset from "../../../../../../common/Fieldset";
import { useFormContextPlus } from "../../../../../../common/Form";
import { STORAGE_GROUPS, Storage } from "./utils";

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
        options={STORAGE_GROUPS}
        sx={{
          alignSelf: "center",
        }}
      />
      <Tooltip
        title={t("study.modelization.storages.injectionNominalCapacity.info")}
        arrow
        placement="top"
      >
        <Box>
          <NumberFE
            label={t("study.modelization.storages.injectionNominalCapacity")}
            name="injectionNominalCapacity"
            control={control}
            rules={{
              min: {
                value: 0,
                message: t("form.field.minValue", { 0: 0 }),
              },
            }}
          />
        </Box>
      </Tooltip>
      <Tooltip
        title={t("study.modelization.storages.withdrawalNominalCapacity.info")}
        arrow
        placement="top"
      >
        <Box>
          <NumberFE
            label={t("study.modelization.storages.withdrawalNominalCapacity")}
            name="withdrawalNominalCapacity"
            control={control}
            rules={{
              min: {
                value: 0,
                message: t("form.field.minValue", { 0: 0 }),
              },
            }}
          />
        </Box>
      </Tooltip>
      <Tooltip
        title={t("study.modelization.storages.reservoirCapacity.info")}
        arrow
        placement="top"
      >
        <Box>
          <NumberFE
            label={t("study.modelization.storages.reservoirCapacity")}
            name="reservoirCapacity"
            control={control}
            rules={{
              min: {
                value: 0,
                message: t("form.field.minValue", { 0: 0 }),
              },
            }}
          />
        </Box>
      </Tooltip>

      <NumberFE
        label={t("study.modelization.storages.efficiency")}
        name="efficiency"
        control={control}
        rules={{
          min: {
            value: 0,
            message: t("form.field.minValue", { 0: 0 }),
          },
          max: {
            value: 100,
            message: t("form.field.maxValue", { 0: 100 }),
          },
        }}
      />
      <NumberFE
        label={t("study.modelization.storages.initialLevel")}
        name="initialLevel"
        control={control}
        rules={{
          min: {
            value: 0,
            message: t("form.field.minValue", { 0: 0 }),
          },
          max: {
            value: 100,
            message: t("form.field.maxValue", { 0: 100 }),
          },
        }}
      />
      <SwitchFE
        label={t("study.modelization.storages.initialLevelOptim")}
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
