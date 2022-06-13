import {
  Box,
  FormControlLabel,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { Controller } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../services/api/study";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../common/Fieldset";
import { FormObj } from "../../../../../common/Form";
import ColorPicker from "./ColorPicker";
import { stringToRGB } from "./ColorPicker/utils";
import { getPropertiesPath, PropertiesFields } from "./utils";

export default function PropertiesForm(
  props: FormObj<PropertiesFields, unknown> & {
    studyId: string;
    areaName: string;
  }
) {
  const { control, register, watch, defaultValues, studyId, areaName } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const filterOptions = ["hourly", "daily", "weekly", "monthly", "annual"].map(
    (item) => ({
      name: t(`study.${item}`),
      value: item,
    })
  );
  const path = useMemo(() => {
    return getPropertiesPath(areaName);
  }, [areaName]);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleAutoSubmit = async (path: string, data: any) => {
    try {
      await editStudy(data, studyId, path);
    } catch (error) {
      enqueueErrorSnackbar(t("study.error.updateUI"), error as AxiosError);
    }
  };

  const renderFilter = (filterName: string) => (
    <SelectFE
      sx={{ mr: 1 }}
      multiple
      {...register(filterName, {
        onAutoSubmit: (value) => {
          const selection = value
            ? (value as Array<string>).filter((val) => val !== "")
            : [];
          handleAutoSubmit(path[filterName], selection.join(", "));
        },
      })}
      renderValue={(value: unknown) => {
        const selection = value
          ? (value as Array<string>).filter((val) => val !== "")
          : [];
        return selection.length > 0
          ? selection.map((elm) => t(`study.${elm}`)).join(", ")
          : t("global.none");
      }}
      defaultValue={(defaultValues || {})[filterName] || []}
      variant="filled"
      options={filterOptions}
    />
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
        <Fieldset title={t("global.general")} style={{ padding: "16px" }}>
          <Box
            sx={{
              width: "100%",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <TextField
              sx={{ mx: 1 }}
              label={t("study.modelization.map.areaName")}
              variant="filled"
              value={defaultValues?.name}
              InputLabelProps={
                defaultValues?.name !== undefined ? { shrink: true } : {}
              }
              disabled
            />
            <ColorPicker
              currentColor={defaultValues?.color}
              {...register("color", {
                onAutoSubmit: (value) => {
                  const color = stringToRGB(value);
                  if (color) {
                    handleAutoSubmit(path.color, {
                      color_r: color.r,
                      color_g: color.g,
                      color_b: color.b,
                      x: watch("posX"),
                      y: watch("posY"),
                    });
                  }
                },
              })}
            />
            <TextField
              sx={{ mx: 1 }}
              type="number"
              label={t("study.modelization.posX")}
              variant="filled"
              placeholder={defaultValues?.posX?.toString()}
              InputLabelProps={
                defaultValues?.posX !== undefined ? { shrink: true } : {}
              }
              {...register("posX", {
                onAutoSubmit: (value) => handleAutoSubmit(path.posX, value),
              })}
            />
            <TextField
              sx={{ mx: 1 }}
              type="number"
              label={t("study.modelization.posY")}
              variant="filled"
              placeholder={defaultValues?.posY?.toString()}
              InputLabelProps={
                defaultValues?.posY !== undefined ? { shrink: true } : {}
              }
              {...register("posY", {
                onAutoSubmit: (value) => handleAutoSubmit(path.posY, value),
              })}
            />
          </Box>
        </Fieldset>
        <Fieldset
          title={t("study.modelization.nodalOptimization")}
          style={{ padding: "16px" }}
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Typography>{`${t(
              "study.modelization.energyCost"
            )} (€/Wh)`}</Typography>
            <Box
              sx={{
                width: "100%",
                display: "flex",
                mt: 1,
              }}
            >
              <TextField
                label={t("study.modelization.unsupplied")}
                variant="filled"
                placeholder={defaultValues?.energieCostUnsupplied?.toString()}
                InputLabelProps={
                  defaultValues?.energieCostUnsupplied !== undefined
                    ? { shrink: true }
                    : {}
                }
                {...register("energieCostUnsupplied", {
                  onAutoSubmit: (value) =>
                    handleAutoSubmit(path.energieCostUnsupplied, value),
                })}
              />
              <TextField
                sx={{ mx: 1 }}
                label={t("study.modelization.splilled")}
                variant="filled"
                placeholder={defaultValues?.energieCostSpilled?.toString()}
                InputLabelProps={
                  defaultValues?.energieCostSpilled !== undefined
                    ? { shrink: true }
                    : {}
                }
                {...register("energieCostSpilled", {
                  onAutoSubmit: (value) =>
                    handleAutoSubmit(path.energieCostSpilled, value),
                })}
              />
            </Box>
          </Box>
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              mt: 4,
            }}
          >
            <Typography>
              {t("study.modelization.lastResortShedding")}
            </Typography>
            <Box
              sx={{
                width: "100%",
                display: "flex",
                mt: 1,
              }}
            >
              <FormControlLabel
                control={
                  <Controller
                    control={control}
                    name="nonDispatchPower"
                    defaultValue={defaultValues?.nonDispatchPower}
                    render={({ field: { value, ref, ...rest } }) => (
                      <Switch checked={value} inputRef={ref} {...rest} />
                    )}
                  />
                }
                label={t("study.modelization.nonDispatchPower")}
              />
              <FormControlLabel
                control={
                  <Controller
                    control={control}
                    name="dispatchHydroPower"
                    defaultValue={defaultValues?.dispatchHydroPower}
                    render={({ field: { value, ref, ...rest } }) => (
                      <Switch checked={value} inputRef={ref} {...rest} />
                    )}
                  />
                }
                label={t("study.modelization.dispatchHydroPower")}
              />
              <FormControlLabel
                control={
                  <Controller
                    control={control}
                    name="otherDispatchPower"
                    defaultValue={defaultValues?.otherDispatchPower}
                    render={({ field: { value, ref, ...rest } }) => (
                      <Switch checked={value} inputRef={ref} {...rest} />
                    )}
                  />
                }
                label={t("study.modelization.otherDispatchPower")}
              />
            </Box>
          </Box>
        </Fieldset>
        <Fieldset title={t("global.filter")} style={{ padding: "16px" }}>
          <Box
            sx={{
              width: "100%",
              display: "flex",
            }}
          >
            {renderFilter("filterSynthesis")}
            {renderFilter("filterByYear")}
          </Box>
        </Fieldset>
      </Box>
    </Box>
  );
}
