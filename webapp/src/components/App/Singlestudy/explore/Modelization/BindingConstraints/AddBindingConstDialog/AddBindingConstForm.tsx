import { useTranslation } from "react-i18next";
import { TextField, Box } from "@mui/material";
import { FormObj } from "../../../../../../common/Form";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import { Root } from "../style";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";

function AddClusterForm(props: FormObj) {
  const {
    register,
    formState: { errors },
    defaultValues,
  } = props;

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

  const renderInput = (
    fielsId: string,
    transId: string,
    required?: boolean
  ) => (
    <TextField
      sx={{ mx: 0, mb: 2 }}
      variant="filled"
      autoFocus
      label={t(transId)}
      error={!!errors[fielsId]}
      helperText={errors[fielsId]?.message}
      placeholder={defaultValues?.[fielsId]}
      InputLabelProps={
        // Allow to show placeholder when field is empty
        defaultValues?.[fielsId] ? { shrink: true } : {}
      }
      fullWidth
      {...register(fielsId, {
        required:
          required === true ? (t("form.field.required") as string) : undefined,
      })}
    />
  );

  const renderSelect = (
    fieldId: string,
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
        {...register(fieldId, {
          required: t("form.field.required") as string,
        })}
        defaultValue={(defaultValues || {})[fieldId] || []}
        variant="filled"
        options={options}
        formControlProps={{
          sx: {
            flex: 1,
            boxSizing: "border-box",
          },
        }}
        sx={{ width: "auto", minWidth: "250px" }}
        label={t(
          transId !== undefined
            ? transId
            : `study.modelization.bindingConst.${fieldId}`
        )}
      />
    </Box>
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <SwitchFE
        sx={{ mx: 0, mb: 2 }}
        label={t("study.modelization.bindingConst.enabled")}
        {...register("enabled")}
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
