import { Box, TextField } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../../services/api/study";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../../common/Fieldset";
import {
  AutoSubmitHandler,
  useFormContext,
} from "../../../../../../../common/Form";
import { getRenewablePath, RenewableFields } from "./utils";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import { Content, Root } from "./style";
import MatrixInput from "../../../../../../../common/MatrixInput";

interface Props {
  area: string;
  cluster: string;
  study: StudyMetadata;
  groupList: Array<string>;
}
export default function ThermalForm(props: Props) {
  const { groupList, study, area, cluster } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const {
    register,
    formState: { errors },
    defaultValues,
  } = useFormContext<RenewableFields>();
  const path = useMemo(() => {
    return getRenewablePath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const tsModeOptions = ["power generation", "production factor"].map(
    (item) => ({ label: item, value: item })
  );

  const groupOptions = groupList.map((item) => ({ label: item, value: item }));

  const pathPrefix = `input/renewables/clusters/${area}/list/${cluster}`;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (
    name: string,
    path: string,
    data: any,
    defaultValue: any
  ) => {
    try {
      if (data === defaultValue || data === undefined) {
        const tmpValues = { ...defaultValues };
        if (name in tmpValues) delete tmpValues[name];
        await editStudy(tmpValues, studyId, pathPrefix);
      } else {
        await editStudy(data, studyId, path);
      }
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const renderSelect = (
    fieldId: string,
    options: Array<{ label: string; value: string }>,
    first?: boolean,
    onAutoSubmit?: AutoSubmitHandler<RenewableFields, string>
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
              handleAutoSubmit(
                fieldId,
                path[fieldId],
                value,
                options.length > 0 ? options[0] : ""
              );
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
        label={t(`study.modelization.clusters.${fieldId}`)}
      />
    </Box>
  );

  return (
    <Root>
      <Fieldset legend={t("global.general")} style={{ padding: "16px" }}>
        <Content>
          <TextField
            sx={{ flex: 1, mr: 1 }}
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
              onAutoSubmit: (value) =>
                handleAutoSubmit("name", path.name, value, ""),
            })}
          />
          {renderSelect("group", groupOptions)}
          {renderSelect("tsInterpretation", tsModeOptions)}
        </Content>
      </Fieldset>
      <Fieldset
        legend={t("study.modelization.clusters.operatingParameters")}
        style={{ padding: "16px" }}
      >
        <Box
          sx={{
            width: "100%",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Content>
            <SwitchFE
              label={t("study.modelization.clusters.enabled")}
              {...register("enabled", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("enabled", path.enabled, value, true),
              })}
            />
            <TextField
              sx={{ mr: 2 }}
              label={t("study.modelization.clusters.unitcount")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.unitcount?.toString()}
              InputLabelProps={
                defaultValues?.unitcount !== undefined ? { shrink: true } : {}
              }
              {...register("unitcount", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("unitcount", path.unitcount, value, 0),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.nominalCapacity")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.nominalCapacity?.toString()}
              InputLabelProps={
                defaultValues?.nominalCapacity !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("nominalCapacity", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(
                    "nominalCapacity",
                    path.nominalCapacity,
                    value,
                    0
                  ),
              })}
            />
          </Content>
        </Box>
      </Fieldset>
      <Box
        sx={{
          width: "100%",
          display: "flex",
          flexDirection: "column",
          height: "500px",
        }}
      >
        <MatrixInput
          study={study}
          url={`input/renewables/series/${area}/${cluster}/series`}
          computStats={MatrixStats.NOCOL}
        />
      </Box>
    </Root>
  );
}
