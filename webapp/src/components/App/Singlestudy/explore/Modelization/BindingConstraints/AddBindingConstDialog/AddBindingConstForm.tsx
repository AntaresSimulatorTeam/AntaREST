import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { FieldPath } from "react-hook-form";
import { useMemo } from "react";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import { Root } from "../style";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { CreateBindingConstraint } from "../../../../Commands/Edition/commandTypes";
import StringFE from "../../../../../../common/fieldEditors/StringFE";
import { useFormContextPlus } from "../../../../../../common/Form";

function AddClusterForm() {
  const { control } = useFormContextPlus<CreateBindingConstraint>();

  const { t } = useTranslation();
  const operatorOptions = useMemo(
    () =>
      ["less", "equal", "greater", "both"].map((item) => ({
        label: t(`study.modelization.bindingConst.operator.${item}`),
        value: item,
      })),
    [t]
  );

  const typeOptions = useMemo(
    () =>
      ["hourly", "daily", "weekly"].map((item) => ({
        label: t(`global.time.${item}`),
        value: item,
      })),
    [t]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const renderInput = (
    name: FieldPath<CreateBindingConstraint>,
    transId: string,
    required?: boolean
  ) => (
    <StringFE
      name={name}
      sx={{ mx: 0, mb: 2, flex: 1 }}
      label={t(transId)}
      variant="filled"
      control={control}
      fullWidth
      rules={{
        required:
          required === true ? (t("form.field.required") as string) : undefined,
      }}
    />
  );

  const renderSelect = (
    name: FieldPath<CreateBindingConstraint>,
    options: Array<{ label: string; value: string }>,
    transId?: string
  ) => (
    <Box
      sx={{
        display: "flex",
        width: "auto",
        mb: 2,
      }}
    >
      <SelectFE
        name={name}
        label={t(
          transId !== undefined
            ? transId
            : `study.modelization.bindingConst.${name}`
        )}
        options={options}
        control={control}
        sx={{ width: "auto", minWidth: "250px" }}
        rules={{
          required: t("form.field.required") as string,
        }}
      />
    </Box>
  );

  return (
    <Root>
      <SwitchFE
        name="enabled"
        label={t("study.modelization.bindingConst.enabled")}
        control={control}
      />
      {renderInput("name", "global.name", true)}
      {renderInput("comments", "study.modelization.bindingConst.comments")}
      {renderSelect(
        "time_step",
        typeOptions,
        "study.modelization.bindingConst.type"
      )}
      {renderSelect("operator", operatorOptions)}
    </Root>
  );
}

export default AddClusterForm;
