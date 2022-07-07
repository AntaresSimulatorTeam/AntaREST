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
import { getThermalPath, ThermalFields } from "./utils";
import SwitchFE from "../../../../../../../common/fieldEditors/SwitchFE";
import { StudyMetadata } from "../../../../../../../../common/types";
import SelectFE from "../../../../../../../common/fieldEditors/SelectFE";
import ThermalMatrixView from "./ThermalMatrixView";
import { Content, Root } from "./style";

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
    defaultValues,
    formState: { errors },
  } = useFormContext<ThermalFields>();
  const path = useMemo(() => {
    return getThermalPath(area, cluster);
  }, [area, cluster]);
  const studyId = study.id;

  const genTsOptions = [
    "use global parameter",
    "force no generation",
    "force generation",
  ].map((item) => ({ label: item, value: item }));

  const groupOptions = groupList.map((item) => ({ label: item, value: item }));

  const lawOptions = ["uniform", "geometric"].map((item) => ({
    label: item,
    value: item,
  }));

  const pathPrefix = `input/thermal/clusters/${area}/list/${cluster}`;

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
    onAutoSubmit?: AutoSubmitHandler<ThermalFields, string>
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
            // autoFocus
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
            <SwitchFE
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.mustRun")}
              {...register("mustRun", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("mustRun", path.mustRun, value, false),
              })}
            />
          </Content>
          <Content sx={{ my: 3 }}>
            <TextField
              sx={{ mr: 2 }}
              label={t("study.modelization.clusters.unitcount")}
              variant="filled"
              type="number"
              error={!!errors.unitcount}
              helperText={errors.unitcount?.message}
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
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.minStablePower")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.minStablePower?.toString()}
              InputLabelProps={
                defaultValues?.minStablePower !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("minStablePower", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(
                    "minStablePower",
                    path.minStablePower,
                    value,
                    0
                  ),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.spinning")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.spinning?.toString()}
              InputLabelProps={
                defaultValues?.spinning !== undefined ? { shrink: true } : {}
              }
              {...register("spinning", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("spinning", path.spinning, value, 0),
              })}
            />
          </Content>
          <Content sx={{ my: 3 }}>
            <TextField
              sx={{ mr: 2 }}
              label={t("study.modelization.clusters.minUpTime")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.minUpTime?.toString()}
              InputLabelProps={
                defaultValues?.minUpTime !== undefined ? { shrink: true } : {}
              }
              {...register("minUpTime", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("minUpTime", path.minUpTime, value, 1),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.minDownTime")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.minDownTime?.toString()}
              InputLabelProps={
                defaultValues?.minDownTime !== undefined ? { shrink: true } : {}
              }
              {...register("minDownTime", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("minDownTime", path.minDownTime, value, 1),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.co2")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.co2?.toString()}
              InputLabelProps={
                defaultValues?.co2 !== undefined ? { shrink: true } : {}
              }
              {...register("co2", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("co2", path.co2, value, 0),
              })}
            />
          </Content>
        </Box>
      </Fieldset>
      <Fieldset
        legend={t("study.modelization.clusters.operatingCosts")}
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
            <TextField
              sx={{ mr: 2 }}
              label={t("study.modelization.clusters.marginalCost")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.marginalCost?.toString()}
              InputLabelProps={
                defaultValues?.marginalCost !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("marginalCost", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("marginalCost", path.marginalCost, value, 0),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.fixedCost")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.fixedCost?.toString()}
              InputLabelProps={
                defaultValues?.fixedCost !== undefined ? { shrink: true } : {}
              }
              {...register("fixedCost", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("fixedCost", path.fixedCost, value, 0),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.startupCost")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.startupCost?.toString()}
              InputLabelProps={
                defaultValues?.startupCost !== undefined ? { shrink: true } : {}
              }
              {...register("startupCost", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("startupCost", path.startupCost, value, 0),
              })}
            />
          </Content>
          <Content sx={{ my: 3 }}>
            <TextField
              sx={{ mr: 2 }}
              label={t("study.modelization.clusters.marketBidCost")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.marketBidCost?.toString()}
              InputLabelProps={
                defaultValues?.marketBidCost !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("marketBid", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(
                    "marketBidCost",
                    path.marketBidCost,
                    value,
                    0
                  ),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.spreadCost")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.spreadCost?.toString()}
              InputLabelProps={
                defaultValues?.spreadCost !== undefined ? { shrink: true } : {}
              }
              {...register("spread", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit("spreadCost", path.spreadCost, value, 0),
              })}
            />
          </Content>
        </Box>
      </Fieldset>
      <Fieldset
        legend={t("study.modelization.clusters.timeSeriesGen")}
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
            {renderSelect("genTs", genTsOptions, true)}
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.volatilityForced")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.volatilityForced?.toString()}
              InputLabelProps={
                defaultValues?.volatilityForced !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("volatilityForced", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(
                    "volatilityForced",
                    path.volatilityForced,
                    value,
                    0
                  ),
              })}
            />
            <TextField
              sx={{ mx: 2 }}
              label={t("study.modelization.clusters.volatilityPlanned")}
              variant="filled"
              type="number"
              placeholder={defaultValues?.volatilityPlanned?.toString()}
              InputLabelProps={
                defaultValues?.volatilityPlanned !== undefined
                  ? { shrink: true }
                  : {}
              }
              {...register("volatilityPlanned", {
                onAutoSubmit: (value) =>
                  handleAutoSubmit(
                    "volatilityPlanned",
                    path.volatilityPlanned,
                    value,
                    0
                  ),
              })}
            />
          </Content>
          <Content sx={{ my: 3 }}>
            {renderSelect("lawForced", lawOptions, true)}
            {renderSelect("lawPlanned", lawOptions)}
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
        <ThermalMatrixView study={study} area={area} cluster={cluster} />
      </Box>
    </Root>
  );
}
