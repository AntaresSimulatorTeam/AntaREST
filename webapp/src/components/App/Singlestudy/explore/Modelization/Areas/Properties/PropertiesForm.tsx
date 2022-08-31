import { Box, TextField, Typography } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import { UseFormReturnPlus } from "../../../../../../common/Form";
import ColorPickerFE from "../../../../../../common/fieldEditors/ColorPickerFE";
import { stringToRGB } from "../../../../../../common/fieldEditors/ColorPickerFE/utils";
import { getPropertiesPath, PropertiesFields } from "./utils";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";

export default function PropertiesForm(
  props: UseFormReturnPlus<PropertiesFields, unknown> & {
    studyId: string;
    areaName: string;
    studyVersion: number;
  }
) {
  const { control, getValues, defaultValues, studyId, areaName, studyVersion } =
    props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
  const filterOptions = ["hourly", "daily", "weekly", "monthly", "annual"].map(
    (item) => ({
      label: t(`global.time.${item}`),
      value: item,
    })
  );
  const adequacyPatchModeOptions = ["inside", "outside", "virtual"].map(
    (item) => ({
      label: item,
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
    <Box sx={{ mb: 2 }}>
      <SelectFE
        name={filterName}
        sx={{ minWidth: "200px" }}
        label={t(`study.modelization.nodeProperties.${filterName}`)}
        multiple
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
        control={control}
        rules={{
          onAutoSubmit: (value) => {
            const selection = value
              ? (value as Array<string>).filter((val) => val !== "")
              : [];
            handleAutoSubmit(path[filterName], selection.join(", "));
          },
        }}
      />
    </Box>
  );

  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        p: 2,
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Fieldset legend={t("global.general")}>
          <TextField
            label={t("study.modelization.map.areaName")}
            variant="filled"
            value={defaultValues?.name}
            InputLabelProps={
              defaultValues?.name !== undefined ? { shrink: true } : {}
            }
            disabled
          />
          <ColorPickerFE
            name="color"
            value={defaultValues?.color}
            control={control}
            rules={{
              onAutoSubmit: (value) => {
                const color = stringToRGB(value);
                if (color) {
                  handleAutoSubmit(path.color, {
                    color_r: color.r,
                    color_g: color.g,
                    color_b: color.b,
                    x: getValues("posX"),
                    y: getValues("posY"),
                  });
                }
              },
            }}
          />
          <NumberFE
            name="posX"
            label={t("study.modelization.posX")}
            variant="filled"
            placeholder={defaultValues?.posX?.toString()}
            InputLabelProps={
              defaultValues?.posX !== undefined ? { shrink: true } : {}
            }
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.posX, value),
            }}
          />
          <NumberFE
            name="posY"
            label={t("study.modelization.posY")}
            variant="filled"
            placeholder={defaultValues?.posY?.toString()}
            InputLabelProps={
              defaultValues?.posY !== undefined ? { shrink: true } : {}
            }
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.posY, value),
            }}
          />
        </Fieldset>
        <Fieldset
          legend={t("study.modelization.nodeProperties.nodalOptimization")}
        >
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
              }}
            >
              <Typography>{`${t(
                "study.modelization.nodeProperties.energyCost"
              )} (€/Wh)`}</Typography>
              <Box
                sx={{
                  width: "100%",
                  display: "flex",
                  mt: 1,
                }}
              >
                <NumberFE
                  name="energieCostUnsupplied"
                  label={t("study.modelization.nodeProperties.unsupplied")}
                  variant="filled"
                  placeholder={defaultValues?.energieCostUnsupplied?.toString()}
                  InputLabelProps={
                    defaultValues?.energieCostUnsupplied !== undefined
                      ? { shrink: true }
                      : {}
                  }
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.energieCostUnsupplied, value),
                  }}
                />
                <NumberFE
                  name="energieCostSpilled"
                  sx={{ mx: 1 }}
                  label={t("study.modelization.nodeProperties.splilled")}
                  variant="filled"
                  placeholder={defaultValues?.energieCostSpilled?.toString()}
                  InputLabelProps={
                    defaultValues?.energieCostSpilled !== undefined
                      ? { shrink: true }
                      : {}
                  }
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.energieCostSpilled, value),
                  }}
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
                {t("study.modelization.nodeProperties.lastResortShedding")}
              </Typography>
              <Box
                sx={{
                  width: "100%",
                  display: "flex",
                  mt: 1,
                }}
              >
                <SwitchFE
                  name="nonDispatchPower"
                  label={t(
                    "study.modelization.nodeProperties.nonDispatchPower"
                  )}
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.nonDispatchPower, value),
                  }}
                />
                <SwitchFE
                  name="dispatchHydroPower"
                  label={t(
                    "study.modelization.nodeProperties.dispatchHydroPower"
                  )}
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.dispatchHydroPower, value),
                  }}
                />
                <SwitchFE
                  name="otherDispatchPower"
                  label={t(
                    "study.modelization.nodeProperties.otherDispatchPower"
                  )}
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.otherDispatchPower, value),
                  }}
                />
              </Box>
            </Box>
          </Box>
        </Fieldset>
        {studyVersion >= 830 && (
          <Fieldset legend="Adequacy patch">
            <SelectFE
              name="adequacyPatchMode"
              sx={{ minWidth: "200px" }}
              label={t("study.modelization.nodeProperties.adequacyPatchMode")}
              variant="filled"
              options={adequacyPatchModeOptions}
              control={control}
              rules={{
                onAutoSubmit: (value) => {
                  handleAutoSubmit(path.adequacyPatchMode, value);
                },
              }}
            />
          </Fieldset>
        )}
        <Fieldset legend={t("study.modelization.nodeProperties.outputFilter")}>
          {renderFilter("filterSynthesis")}
          {renderFilter("filterByYear")}
        </Fieldset>
      </Box>
    </Box>
  );
}
