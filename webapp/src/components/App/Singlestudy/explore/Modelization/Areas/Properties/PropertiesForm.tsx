import { Box, Typography } from "@mui/material";
import { AxiosError } from "axios";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { editStudy } from "../../../../../../../services/api/study";
import SelectFE from "../../../../../../common/fieldEditors/SelectFE";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import Fieldset from "../../../../../../common/Fieldset";
import ColorPickerFE from "../../../../../../common/fieldEditors/ColorPickerFE";
import { stringToRGB } from "../../../../../../common/fieldEditors/ColorPickerFE/utils";
import { getPropertiesPath, PropertiesFields } from "./utils";
import SwitchFE from "../../../../../../common/fieldEditors/SwitchFE";
import NumberFE from "../../../../../../common/fieldEditors/NumberFE";
import OutputFilters from "../../../common/OutputFilters";
import { UseFormReturnPlus } from "../../../../../../common/Form/types";
import StringFE from "../../../../../../common/fieldEditors/StringFE";

interface Props extends UseFormReturnPlus<PropertiesFields> {
  studyId: string;
  areaName: string;
  studyVersion: number;
}

export default function PropertiesForm(props: Props) {
  const { control, getValues, studyId, areaName, studyVersion } = props;
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [t] = useTranslation();
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
          <StringFE
            label={t("study.modelization.map.areaName")}
            variant="filled"
            name="name"
            control={control}
            disabled
          />
          <ColorPickerFE
            name="color"
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
            control={control}
            rules={{
              onAutoSubmit: (value) => handleAutoSubmit(path.posX, value),
            }}
          />
          <NumberFE
            name="posY"
            label={t("study.modelization.posY")}
            variant="filled"
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
                  name="energyCostUnsupplied"
                  label={t("study.modelization.nodeProperties.unsupplied")}
                  variant="filled"
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.energyCostUnsupplied, value),
                  }}
                />
                <NumberFE
                  name="energyCostSpilled"
                  sx={{ mx: 1 }}
                  label={t("study.modelization.nodeProperties.splilled")}
                  variant="filled"
                  control={control}
                  rules={{
                    onAutoSubmit: (value) =>
                      handleAutoSubmit(path.energyCostSpilled, value),
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
        <OutputFilters
          control={control}
          onAutoSubmit={(filter, value) =>
            handleAutoSubmit(path[filter], value)
          }
        />
      </Box>
    </Box>
  );
}
