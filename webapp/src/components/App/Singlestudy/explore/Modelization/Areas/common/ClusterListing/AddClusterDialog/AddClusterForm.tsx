import { useTranslation } from "react-i18next";
import { TextField, Autocomplete } from "@mui/material";
import { FormObj } from "../../../../../../../../common/Form";

interface OtherProps {
  clusterNameList: Array<string>;
  clusterGroupList: Array<string>;
}

function AddClusterForm(props: FormObj & OtherProps) {
  const {
    register,
    formState: { errors },
    clusterNameList,
    clusterGroupList,
    defaultValues,
  } = props;

  const { t } = useTranslation();

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
          validate: (value) => {
            if (clusterNameList.includes(value)) {
              return t("study.error.form.clusterName") as string;
            }
          },
        })}
      />
      <Autocomplete
        id="add-cluster-dialog-group"
        freeSolo
        options={clusterGroupList}
        placeholder={defaultValues?.group}
        renderInput={(params) => (
          <TextField
            {...params}
            variant="filled"
            error={!!errors.group}
            helperText={errors.group?.message}
            InputLabelProps={
              // Allow to show placeholder when field is empty
              defaultValues?.group ? { shrink: true } : {}
            }
            {...register("group", {
              required: t("form.field.required") as string,
            })}
            inputProps={{
              ...params.inputProps,
              autoComplete: "disabled", // disable autocomplete and autofill
            }}
            label={t("study.modelization.clusters.clusterGroup")}
          />
        )}
      />
    </>
  );
}

export default AddClusterForm;
