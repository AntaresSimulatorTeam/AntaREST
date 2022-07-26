import { useTranslation } from "react-i18next";
import { Box } from "@mui/material";
import { useFormContext } from "react-hook-form";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import { Root } from "../style";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { CreateBindingConstraint } from "../../../../Commands/Edition/commandTypes";
import StringFE from "../../../../../../common/fieldEditors/StringFE";

function AddClusterForm() {
  const { control } = useFormContext<CreateBindingConstraint>();

  const { t } = useTranslation();
  const operatorOptions = ["less", "equal", "greater", "both"].map((item) => ({
    label: t(`study.modelization.bindingConst.operator.${item}`),
    value: item,
  }));

  const typeOptions = ["hourly", "daily", "weekly"].map((item) => ({
    label: t(`study.${item}`),
    value: item,
  }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const renderInput = (name: string, transId: string, required?: boolean) => (
    <StringFE
      name={name}
      sx={{ mx: 0, mb: 2, flex: 1 }}
      label={t(transId)}
      variant="filled"
      control={control}
      fullWidth
      rules={{
        required: t("form.field.required") as string,
      }}
    />
  );

  const renderSelect = (
    name: string,
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
        formControlProps={{
          sx: {
            flex: 1,
            boxSizing: "border-box",
          },
        }}
        sx={{ width: "auto", minWidth: "250px" }}
        rules={{
          required: t("form.field.required") as string,
        }}
      />
    </Box>
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

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
