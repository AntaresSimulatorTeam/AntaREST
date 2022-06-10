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
  const { control, register, defaultValues, studyId, areaName } = props;
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

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        py: 2,
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
            // label={t("study.modelization.map.areaName")}
            variant="filled"
            value={defaultValues?.name}
            disabled
          />
          <ColorPicker
            currentColor={defaultValues?.color}
            {...register("color", {
              setValueAs: (value) => stringToRGB(value),
              onAutoSubmit: (value) => {
                // TODO here we send the color to the path ui, but it also contains x and y which are now set to undefined here
                handleAutoSubmit(path.color, {
                  color_r: value.r,
                  color_g: value.g,
                  color_b: value.b,
                });
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
              // Allow to show placeholder when field is empty
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
          <Typography>{t("study.modelization.lastResortShedding")}</Typography>
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
          <SelectFE
            multiple
            {...register("filterSynthesis", {
              onAutoSubmit: (value) =>
                handleAutoSubmit(
                  path.filterSynthesis,
                  value ? value.join(", ") : ""
                ),
            })}
            renderValue={(value: unknown) =>
              value
                ? (value as Array<string>)
                    .map((elm) => t(`study.${elm}`))
                    .join(",")
                : ""
            }
            defaultValue={defaultValues?.filterSynthesis || []}
            variant="filled"
            options={filterOptions}
          />
          <SelectFE
            multiple
            sx={{ mx: 1 }}
            {...register("filterByYear", {
              onAutoSubmit: (value) =>
                handleAutoSubmit(
                  path.filterByYear,
                  value ? value.join(", ") : ""
                ),
            })}
            renderValue={(value: unknown) =>
              value
                ? (value as Array<string>)
                    .map((elm) => t(`study.${elm}`))
                    .join(",")
                : ""
            }
            defaultValue={defaultValues?.filterByYear || []}
            variant="filled"
            options={filterOptions}
          />
        </Box>
      </Fieldset>
    </Box>
  );
}
