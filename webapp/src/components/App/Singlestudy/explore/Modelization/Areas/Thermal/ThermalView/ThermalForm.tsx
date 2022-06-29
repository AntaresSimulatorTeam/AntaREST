import { Autocomplete, Box, TextField } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../../common/Fieldset";
import { AutoSubmitHandler, FormObj } from "../../../../../../../common/Form";
import { getThermalPath, ThermalFields } from "./utils";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import MatrixInput from "../../../../../../../common/MatrixInput";
import LinkMatrixView from "./LinkMatrixView";

export default function ThermalForm(
  props: FormObj<ThermalFields, unknown> & {
    area: string;
    cluster: string;
    study: StudyMetadata;
    nameList: Array<string>;
    groupList: Array<string>;
  }
) {
  const {
    register,
    formState: { errors },
    defaultValues,
    nameList,
    groupList,
    study,
    area,
    cluster,
  } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const path = useMemo(() => {
    return getThermalPath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (path: string, data: any) => {
    try {
      await editStudy(data, studyId, path);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const renderSelect = (
    fieldId: string,
    options: Array<{ label: string; value: string }>,
    onAutoSubmit?: AutoSubmitHandler<ThermalFields, string>
  ) => (
    <Box sx={{ display: "flex", flexGrow: 1 }}>
      <SelectFE
        {...register(fieldId, {
          onAutoSubmit:
            onAutoSubmit ||
            ((value) => {
              handleAutoSubmit(path[fieldId], value);
            }),
        })}
        defaultValue={(defaultValues || {})[fieldId] || []}
        variant="filled"
        options={options}
        formControlProps={{
          sx: {
            flex: 1,
            mx: 2,
            boxSizing: "border-box",
          },
        }}
        sx={{ width: "100%", minWidth: "200px" }}
        label={t(`study.modelization.links.${fieldId}`)}
      />
    </Box>
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        py: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Fieldset legend={t("global.general")} style={{ padding: "16px" }}>
          <Box
            sx={{
              width: "100%",
              display: "flex",
              justifyContent: "flex-start",
            }}
          >
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
              {...register("name", {
                required: t("form.field.required") as string,
                validate: (value) => {
                  if (nameList.includes(value.toLowerCase())) {
                    return t("study.error.form.clusterName") as string;
                  }
                },
              })}
            />
            <Autocomplete
              id="add-cluster-dialog-group"
              freeSolo
              options={groupList}
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
          </Box>
        </Fieldset>
        <Fieldset
          legend={t("study.modelization.nodeProperties.outputFilter")}
          style={{ padding: "16px" }}
        >
          <Box
            sx={{
              width: "100%",
              display: "flex",
              flexDirection: "column",
            }}
          />
        </Fieldset>
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
            height: "500px",
          }}
        />
      </Box>
    </Box>
  );
}
