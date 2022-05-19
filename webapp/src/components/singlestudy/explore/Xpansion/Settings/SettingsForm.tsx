import { useState, useEffect } from "react";
import { Box, Divider, Typography, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import { XpansionSettings } from "../types";
import {
  Fields,
  SelectFields,
  Title,
  StyledTextField,
  StyledVisibilityIcon,
} from "../share/styles";
import SelectSingle from "../../../../common/SelectSingle";

interface PropType {
  settings: XpansionSettings;
  constraints: Array<string>;
  updateSettings: (value: XpansionSettings) => Promise<void>;
  onRead: (filename: string) => Promise<void>;
}

function SettingsForm(props: PropType) {
  const [t] = useTranslation();
  const { settings, constraints, updateSettings, onRead } = props;
  const [currentSettings, setCurrentSettings] =
    useState<XpansionSettings>(settings);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);

  const ucType = ["expansion_fast", "expansion_accurate"];
  const master = ["relaxed", "integer"];
  const solver = ["Cbc", "Xpress"];
  const cutType = ["yearly", "weekly", "average"];

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    setCurrentSettings({ ...currentSettings, [key]: value });
  };

  useEffect(() => {
    if (settings) {
      setCurrentSettings(settings);
      setSaveAllowed(false);
    }
  }, [settings]);

  return (
    <Box sx={{ px: 1 }}>
      <Box>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="flex-end"
        >
          <Title>{t("global:global.settings")}</Title>
          <Button
            variant="outlined"
            color="primary"
            sx={{
              display: "flex",
              flexFlow: "row nowrap",
              justifyContent: "space-between",
              alignItems: "center",
              height: "30px",
              mr: 1,
              border: "2px solid",
            }}
            onClick={() => {
              updateSettings(currentSettings);
              setSaveAllowed(false);
            }}
            disabled={!saveAllowed}
          >
            <SaveIcon sx={{ m: 0.2, width: "16px", height: "16px" }} />
            <Typography sx={{ m: 0.2, fontSize: "12px" }}>
              {t("global:global.save")}
            </Typography>
          </Button>
        </Box>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <SelectFields sx={{ mb: 1 }}>
            <SelectSingle
              name="uc_type"
              list={ucType.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.ucType")}
              data={currentSettings.uc_type}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          <SelectFields sx={{ mb: 1 }}>
            <SelectSingle
              name="master"
              list={master.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.master")}
              data={currentSettings.master}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          <StyledTextField
            type="number"
            label={t("global:xpansion.optimalyGap")}
            variant="filled"
            value={currentSettings.optimality_gap}
            onChange={(e) =>
              handleChange("optimality_gap", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
          />
          <StyledTextField
            label={t("global:xpansion.maxIteration")}
            variant="filled"
            value={currentSettings.max_iteration || ""}
            onChange={(e) =>
              handleChange("max_iteration", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
          />
          <StyledTextField
            type="number"
            label={t("global:xpansion.relaxedOptimalityGap")}
            variant="filled"
            value={currentSettings["relaxed-optimality-gap"] || ""}
            onChange={(e) =>
              handleChange("relaxed-optimality-gap", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
          />
          <SelectFields sx={{ mb: 1 }}>
            <SelectSingle
              name="cut-type"
              list={cutType.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.cutType")}
              data={currentSettings["cut-type"] || ""}
              sx={{
                minWidth: "100%",
              }}
              handleChange={handleChange}
              optional
            />
          </SelectFields>
          <StyledTextField
            label={t("global:xpansion.amplSolver")}
            variant="filled"
            value={currentSettings["ampl.solver"] || ""}
            onChange={(e) => handleChange("ampl.solver", e.target.value)}
            sx={{ mb: 1 }}
          />
          <StyledTextField
            type="number"
            label={t("global:xpansion.amplPresolve")}
            variant="filled"
            value={currentSettings["ampl.presolve"] || ""}
            onChange={(e) =>
              handleChange("ampl.presolve", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
          />
          <StyledTextField
            type="number"
            label={t("global:xpansion.amplSolverBoundsFrequency")}
            variant="filled"
            value={currentSettings["ampl.solve_bounds_frequency"] || ""}
            onChange={(e) =>
              handleChange(
                "ampl.solve_bounds_frequency",
                parseFloat(e.target.value)
              )
            }
            sx={{ mb: 1 }}
          />
          <StyledTextField
            type="number"
            label={t("global:xpansion.relativeGap")}
            variant="filled"
            value={currentSettings.relative_gap || ""}
            onChange={(e) =>
              handleChange("relative_gap", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
          />
          <SelectFields sx={{ mb: 1 }}>
            <SelectSingle
              name="solver"
              list={solver.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.solver")}
              data={currentSettings.solver || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
          </SelectFields>
        </Fields>
      </Box>
      <Box>
        <Title>{t("global:xpansion.extra")}</Title>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            width: "100%",
            mb: 2,
            "&> div": {
              mr: 2,
              mb: 2,
            },
          }}
        >
          <SelectFields>
            <SelectSingle
              name="yearly-weights"
              list={constraints.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.yearlyWeight")}
              data={currentSettings["yearly-weights"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <StyledVisibilityIcon
              onClick={() =>
                currentSettings["yearly-weights"] &&
                onRead(currentSettings["yearly-weights"] || "")
              }
            />
          </SelectFields>
          <SelectFields>
            <SelectSingle
              name="additional-constraints"
              list={constraints.map((item) => {
                return { id: item, name: item };
              })}
              label={t("global:xpansion.additionalConstraints")}
              data={currentSettings["additional-constraints"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <StyledVisibilityIcon
              onClick={() =>
                currentSettings["additional-constraints"] &&
                onRead(currentSettings["additional-constraints"] || "")
              }
            />
          </SelectFields>
        </Box>
      </Box>
    </Box>
  );
}

export default SettingsForm;
