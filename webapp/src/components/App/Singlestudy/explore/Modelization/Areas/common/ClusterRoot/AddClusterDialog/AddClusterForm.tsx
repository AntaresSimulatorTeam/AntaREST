import { useTranslation } from "react-i18next";
import { TextField, Box } from "@mui/material";
import { FormObj } from "../../../../../../../../common/Form";
import SelectFE from "../../../../../../../../common/fieldEditors/SelectFE";

interface OtherProps {
  clusterGroupList: Array<string>;
}

function AddClusterForm(props: FormObj & OtherProps) {
  const {
    register,
    formState: { errors },
    clusterGroupList,
    defaultValues,
  } = props;

  const { t } = useTranslation();
  const groupOptions = clusterGroupList.map((item) => ({
    label: item,
    value: item,
  }));

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/* Name */}
      <TextField
        sx={{ mx: 0, mb: 2 }}
        variant="filled"
        autoFocus
        label={t("global.name")}
        error={!!errors.name}
        helperText={errors.name?.message}
        placeholder={defaultValues?.name}
        InputLabelProps={
          // Allow to show placeholder when field is empty
          defaultValues?.name ? { shrink: true } : {}
        }
        fullWidth
        {...register("name", {
          required: t("form.field.required") as string,
        })}
      />
      <Box
        sx={{
          display: "flex",
          width: "auto",
        }}
      >
        <SelectFE
          {...register("group", {
            required: t("form.field.required") as string,
          })}
          defaultValue={(defaultValues || {}).group || []}
          variant="filled"
          options={groupOptions}
          formControlProps={{
            sx: {
              flex: 1,
              boxSizing: "border-box",
            },
          }}
          sx={{ width: "auto", minWidth: "250px" }}
          label={t(`study.modelization.clusters.group`)}
        />
      </Box>
    </>
  );
}

export default AddClusterForm;
