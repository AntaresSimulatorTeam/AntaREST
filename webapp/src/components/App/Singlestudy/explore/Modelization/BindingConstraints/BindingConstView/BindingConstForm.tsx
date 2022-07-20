import { Box, TextField } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import {
  AutoSubmitHandler,
  useFormContext,
} from "../../../../../../common/Form";
import { getBindingConstPath, BindingConstFields } from "./utils";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import { StudyMetadata } from "../../../../../../../common/types";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import { Content, Root } from "../style";
import Constraint from "./Constraint";

interface Props {
  bcIndex: number;
  study: StudyMetadata;
}

export default function BindingConstForm(props: Props) {
  const { study, bcIndex } = props;
  const studyId = study.id;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const {
    register,
    defaultValues,
    formState: { errors },
  } = useFormContext<BindingConstFields>();
  const path = useMemo(() => {
    return getBindingConstPath(bcIndex);
  }, [bcIndex]);

  const optionOperator = ["less", "equal", "greater", "both"].map((item) => ({
    label: t(`study.modelization.bindingConst.operator.${item}`),
    value: item.toLowerCase(),
  }));

  const typeOptions = ["hourly", "daily", "weekly"].map((item) => ({
    label: t(`study.${item}`),
    value: item,
  }));

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (path: string, data: any) => {
    try {
      console.log("IT'S WORKING");
      await editStudy(data, studyId, path);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const renderSelect = (
    fieldId: string,
    options: Array<{ label: string; value: string }>,
    first?: boolean,
    onAutoSubmit?: AutoSubmitHandler<BindingConstFields, string>
  ) => (
    <Box
      sx={{
        display: "flex",
        width: "auto",
        ...(first === true ? { mr: 2 } : { mx: 2 }),
      }}
    >
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
            boxSizing: "border-box",
          },
        }}
        sx={{ width: "auto", minWidth: "250px" }}
        label={t(`study.modelization.bindingConst.${fieldId}`)}
      />
    </Box>
  );

  return (
    <Root>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Fieldset
          legend={t("global.general")}
          style={{
            padding: "16px",
          }}
        >
          <Content>
            <TextField
              sx={{ mr: 2 }}
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
                onAutoSubmit: (value) => handleAutoSubmit(path.name, value),
              })}
            />
            <TextField
              sx={{ flexGrow: 1 }}
              variant="filled"
              autoFocus
              label={t("study.modelization.bindingConst.comments")}
              error={!!errors.comments}
              helperText={errors.comments?.message}
              placeholder={defaultValues?.comments}
              InputLabelProps={
                // Allow to show placeholder when field is empty
                defaultValues?.comments ? { shrink: true } : {}
              }
              {...register("comments", {
                onAutoSubmit: (value) => handleAutoSubmit(path.comments, value),
              })}
            />
          </Content>
          <Content sx={{ my: 2 }}>
            {renderSelect("type", typeOptions, true)}
            {renderSelect("operator", optionOperator)}
            <SwitchFE
              sx={{ mx: 2 }}
              label={t("study.modelization.bindingConst.enabled")}
              {...register("enabled", {
                onAutoSubmit: (value) => handleAutoSubmit(path.enabled, value),
              })}
            />
          </Content>
        </Fieldset>
        <Fieldset
          legend={t("study.modelization.bindingConst.constraints")}
          style={{ padding: "16px" }}
        >
          <Content>
            <Constraint areaList={[]} />
          </Content>
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
    </Root>
  );
}
