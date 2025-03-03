/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { useState, useEffect } from "react";
import { Box, Divider, Typography, Button, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import SaveIcon from "@mui/icons-material/Save";
import { XpansionResourceType, type XpansionSettings } from "../types";
import { Fields, SelectFields, Title, StyledVisibilityIcon } from "../share/styles";
import SelectSingle from "../../../../../common/SelectSingle";
import NumberFE from "../../../../../common/fieldEditors/NumberFE";
import SelectFE from "../../../../../common/fieldEditors/SelectFE";
import SwitchFE from "../../../../../common/fieldEditors/SwitchFE";

interface PropType {
  settings: XpansionSettings;
  constraints: string[];
  weights: string[];
  candidates: string[];
  updateSettings: (value: XpansionSettings) => Promise<void>;
  onRead: (resourceType: string, filename: string) => Promise<void>;
}

function SettingsForm(props: PropType) {
  const [t] = useTranslation();
  const { settings, constraints, weights, candidates, updateSettings, onRead } = props;
  const [currentSettings, setCurrentSettings] = useState<XpansionSettings>(settings);
  const [saveAllowed, setSaveAllowed] = useState<boolean>(false);

  const ucType = ["expansion_fast", "expansion_accurate"];
  const master = ["relaxed", "integer"];
  const solver = ["Cbc", "Xpress"];

  const handleChange = (key: string, value: string | number) => {
    setSaveAllowed(true);
    setCurrentSettings({ ...currentSettings, [key]: value });
  };

  const handleObjectChange = (
    objectKey: keyof XpansionSettings,
    key: string,
    value: string | number | boolean | string[],
  ) => {
    setSaveAllowed(true);
    setCurrentSettings((prevSettings) => ({
      ...prevSettings,
      [objectKey]: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ...(prevSettings[objectKey] as Record<string, any>),
        [key]: value,
      },
    }));
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
        <Box display="flex" justifyContent="space-between" alignItems="flex-end">
          <Title>{t("xpansion.optimization")}</Title>
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
            <Typography sx={{ m: 0.2, fontSize: "12px" }}>{t("global.save")}</Typography>
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
              label={t("xpansion.ucType")}
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
              label={t("xpansion.master")}
              data={currentSettings.master}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          <TextField
            type="number"
            label={t("xpansion.maxIteration")}
            value={currentSettings.max_iteration}
            onChange={(e) => handleChange("max_iteration", e.target.value)}
            sx={{ mb: 1 }}
            inputProps={{ min: 1, max: 1000, step: 1 }}
          />
          <TextField
            type="number"
            label={t("xpansion.optimalityGap")}
            value={currentSettings.optimality_gap}
            onChange={(e) => handleChange("optimality_gap", parseFloat(e.target.value))}
            sx={{ mb: 1 }}
            inputProps={{ min: 0 }}
          />
          <TextField
            type="number"
            label={t("xpansion.relativeGap")}
            value={currentSettings.relative_gap}
            onChange={(e) => handleChange("relative_gap", parseFloat(e.target.value))}
            sx={{ mb: 1 }}
            inputProps={{ min: 0 }}
          />
          <TextField
            type="number"
            label={t("xpansion.relaxedOptimalityGap")}
            value={currentSettings.relaxed_optimality_gap}
            onChange={(e) => handleChange("relaxed_optimality_gap", e.target.value)}
            sx={{ mb: 1 }}
            inputProps={{ min: 0 }}
          />
          <SelectFields sx={{ mb: 1 }}>
            <SelectSingle
              name="solver"
              list={solver.map((item) => {
                return { id: item, name: item };
              })}
              label={t("xpansion.solver")}
              data={currentSettings.solver}
              handleChange={handleChange}
              sx={{
                minWidth: "100%",
              }}
            />
          </SelectFields>
          {/* <TextField
            type="number"
            label={t("xpansion.timeLimit")}
            
            value={Math.round((currentSettings.timelimit || 1e12) / 3600)}
            onChange={(e) =>
              handleChange(
                "timelimit",
                Math.round(parseFloat(e.target.value) * 3600),
              )
            }
            sx={{ mb: 1 }}
          /> */}
          <TextField
            type="number"
            label={t("xpansion.separationParameter")}
            value={currentSettings.separation_parameter}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              handleChange("separation_parameter", parseFloat(e.target.value))
            }
            sx={{ mb: 1 }}
            inputProps={{ min: 0, max: 1, step: 0.05 }}
          />
          <TextField
            type="number"
            label={t("xpansion.batchSize")}
            value={currentSettings.batch_size}
            onChange={(e) => handleChange("batch_size", parseInt(e.target.value, 10))}
            sx={{ mb: 1 }}
            inputProps={{ min: 0 }}
          />
          <TextField
            type="number"
            label={t("xpansion.logLevel")}
            value={currentSettings.log_level}
            onChange={(e) => handleChange("log_level", parseInt(e.target.value, 10))}
            inputProps={{ min: 0, max: 3, step: 1 }}
            sx={{ mb: 1 }}
          />
        </Fields>
      </Box>
      <Box>
        <Title>{t("xpansion.extra")}</Title>
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
              list={weights.map((item) => {
                return { id: item, name: item };
              })}
              label={t("xpansion.yearlyWeight")}
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
                onRead(XpansionResourceType.weights, currentSettings["yearly-weights"] || "")
              }
            />
          </SelectFields>
          <SelectFields>
            <SelectSingle
              name="additional-constraints"
              list={constraints.map((item) => {
                return { id: item, name: item };
              })}
              label={t("xpansion.additionalConstraints")}
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
                onRead(
                  XpansionResourceType.constraints,
                  currentSettings["additional-constraints"] || "",
                )
              }
            />
          </SelectFields>
        </Box>
      </Box>
      <Box>
        <Title>{t("xpansion.sensitivity")}</Title>
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
          <NumberFE
            value={currentSettings.sensitivity_config?.epsilon}
            label={t("xpansion.epsilon")}
            onChange={(e) =>
              handleObjectChange("sensitivity_config", "epsilon", parseFloat(e.target.value))
            }
            inputProps={{ min: 0 }}
          />
          <SwitchFE
            value={currentSettings.sensitivity_config?.capex}
            label={t("xpansion.capex")}
            onChange={(e, checked) => handleObjectChange("sensitivity_config", "capex", checked)}
          />
          <SelectFE
            sx={{ minWidth: "200px" }}
            label={t("xpansion.projection")}
            multiple
            value={currentSettings.sensitivity_config?.projection || []}
            onChange={(e) =>
              handleObjectChange("sensitivity_config", "projection", e.target.value as string[])
            }
            options={candidates}
          />
        </Box>
      </Box>
    </Box>
  );
}

export default SettingsForm;
