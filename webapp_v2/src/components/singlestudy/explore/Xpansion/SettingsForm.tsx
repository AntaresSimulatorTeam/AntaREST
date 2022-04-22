import { useState, useEffect } from "react";
import { Box, Divider, Typography, Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import VisibilityIcon from "@mui/icons-material/Visibility";
import { XpansionSettings } from "../../../../common/types";
import { Fields, SelectFields, Title, StyledTextField } from "./Styles";
import SelectSingle from "../../../common/SelectSingle";

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
    <Box>
      <Box>
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="flex-end"
        >
          <Title>{t("main:settings")}</Title>
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
              {t("main:save")}
            </Typography>
          </Button>
        </Box>
        <Divider sx={{ mt: 1, mb: 2 }} />
        <Fields>
          <SelectFields>
            <SelectSingle
              name={t("xpansion:ucType")}
              list={ucType.map((item) => {
                return { id: item, name: item };
              })}
              label="uc_type"
              data={currentSettings.uc_type}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          <SelectFields>
            <SelectSingle
              name={t("xpansion:master")}
              list={master.map((item) => {
                return { id: item, name: item };
              })}
              label="master"
              data={currentSettings.master}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          <StyledTextField
            type="number"
            label={t("xpansion:optimalyGap")}
            variant="filled"
            value={currentSettings.optimality_gap}
            onChange={(e) =>
              handleChange("optimality_gap", parseFloat(e.target.value))
            }
          />
          <StyledTextField
            label={t("xpansion:maxIteration")}
            variant="filled"
            value={currentSettings.max_iteration || ""}
            onChange={(e) =>
              handleChange("max_iteration", parseFloat(e.target.value))
            }
          />
          <StyledTextField
            type="number"
            label={t("xpansion:relaxedOptimalityGap")}
            variant="filled"
            value={currentSettings["relaxed-optimality-gap"] || ""}
            onChange={(e) =>
              handleChange("relaxed-optimality-gap", parseFloat(e.target.value))
            }
          />
          <SelectFields>
            <SelectSingle
              name={t("xpansion:cutType")}
              list={cutType.map((item) => {
                return { id: item, name: item };
              })}
              label="cut_type"
              data={currentSettings.cut_type || ""}
              sx={{
                minWidth: "100%",
              }}
              handleChange={handleChange}
            />
          </SelectFields>
          <StyledTextField
            label={t("xpansion:amplSolver")}
            variant="filled"
            value={currentSettings["ampl.solver"] || ""}
            onChange={(e) => handleChange("ampl.solver", e.target.value)}
          />
          <StyledTextField
            type="number"
            label={t("xpansion:amplPresolve")}
            variant="filled"
            value={currentSettings["ampl.presolve"] || ""}
            onChange={(e) =>
              handleChange("ampl.presolve", parseFloat(e.target.value))
            }
          />
          <StyledTextField
            type="number"
            label={t("xpansion:amplSolverBoundsFrequency")}
            variant="filled"
            value={currentSettings["ampl.solve_bounds_frequency"] || ""}
            onChange={(e) =>
              handleChange(
                "ampl.solve_bounds_frequency",
                parseFloat(e.target.value)
              )
            }
          />
          <StyledTextField
            type="number"
            label={t("xpansion:relativeGap")}
            variant="filled"
            value={currentSettings.relative_gap || ""}
            onChange={(e) =>
              handleChange("relative_gap", parseFloat(e.target.value))
            }
          />
          <SelectFields>
            <SelectSingle
              name={t("xpansion:solver")}
              list={solver.map((item) => {
                return { id: item, name: item };
              })}
              label="solver"
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
        <Title>{t("xpansion:extra")}</Title>
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
              name={t("xpansion:yearlyWeight")}
              list={constraints.map((item) => {
                return { id: item, name: item };
              })}
              label="yearly-weights"
              data={currentSettings["yearly-weights"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <VisibilityIcon
              sx={{
                mx: 1,
                "&:hover": {
                  color: "secondary.main",
                  cursor: "pointer",
                },
              }}
              color="primary"
              onClick={() =>
                currentSettings["yearly-weights"] &&
                onRead(currentSettings["yearly-weights"] || "")
              }
            />
          </SelectFields>
          <SelectFields>
            <SelectSingle
              name={t("xpansion:additionalConstraints")}
              list={constraints.map((item) => {
                return { id: item, name: item };
              })}
              label="additional-constraints"
              data={currentSettings["additional-constraints"] || ""}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
              optional
            />
            <VisibilityIcon
              sx={{
                mx: 1,
                "&:hover": {
                  color: "secondary.main",
                  cursor: "pointer",
                },
              }}
              color="primary"
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
