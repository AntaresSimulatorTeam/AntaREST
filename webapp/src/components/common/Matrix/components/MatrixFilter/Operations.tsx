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

import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Button,
  Tooltip,
  type SelectChangeEvent,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useTranslation } from "react-i18next";
import type { OperationsProps } from "./types";
import { Operation } from "../../shared/constants";
import { useOperationControls } from "./hooks/useOperationControls";
import { TYPOGRAPHY_STYLES, FORM_STYLES, DESIGN_TOKENS, OPERATION_STYLES } from "./styles";

function Operations({ filter, setFilter, onApplyOperation }: OperationsProps) {
  const { t } = useTranslation();
  const { value, hasValidFilters, handleOperationTypeChange, handleValueChange } =
    useOperationControls({ filter, setFilter, onApplyOperation });

  const getOperationSummary = () => {
    if (!filter.active || !filter.operation.type) {
      return "";
    }

    const operationType = t(`matrix.operation.${filter.operation.type.toLowerCase()}`);
    if (filter.operation.type === Operation.Abs) {
      return operationType;
    }
    return `${operationType} ${filter.operation.value || 0}`;
  };

  const operationSummary = getOperationSummary();

  const handleOperationTypeChangeEvent = (e: SelectChangeEvent<string>) => {
    handleOperationTypeChange(e.target.value);
  };

  const handleValueChangeEvent = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number.parseFloat(e.target.value) || 0;
    handleValueChange(newValue);
  };

  return (
    <Accordion defaultExpanded sx={{ my: DESIGN_TOKENS.spacing.lg, borderTop: "none" }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1, flex: 1 }}>
          <Typography sx={TYPOGRAPHY_STYLES.sectionTitle}>
            {t("matrix.filter.operation")}
          </Typography>
          {operationSummary && (
            <Typography sx={{ ...TYPOGRAPHY_STYLES.smallCaption, color: "text.secondary" }}>
              ({operationSummary})
            </Typography>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={FORM_STYLES.responsiveContainer}>
          <Tooltip title={t("matrix.filter.operationType")} placement="top">
            <FormControl size="small" sx={{ flex: 1, ...FORM_STYLES.sideBySideFormControl }}>
              <InputLabel>{t("matrix.filter.operationType")}</InputLabel>
              <Select
                value={filter.operation.type}
                label={t("matrix.filter.operationType")}
                onChange={handleOperationTypeChangeEvent}
                disabled={!filter.active}
                sx={FORM_STYLES.sideBySideFormControl}
              >
                <MenuItem value={Operation.Eq} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.equal")}
                </MenuItem>
                <MenuItem value={Operation.Add} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.add")}
                </MenuItem>
                <MenuItem value={Operation.Sub} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.subtract")}
                </MenuItem>
                <MenuItem value={Operation.Mul} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.multiply")}
                </MenuItem>
                <MenuItem value={Operation.Div} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.divide")}
                </MenuItem>
                <MenuItem value={Operation.Abs} sx={FORM_STYLES.menuItem}>
                  {t("matrix.operation.absolute")}
                </MenuItem>
              </Select>
            </FormControl>
          </Tooltip>

          {filter.operation.type !== Operation.Abs && (
            <Tooltip title={t("matrix.filter.value")} placement="top">
              <TextField
                label={t("matrix.filter.value")}
                type="number"
                value={value}
                onChange={handleValueChangeEvent}
                size="small"
                sx={{ ...FORM_STYLES.sideBySideFormControl, flex: 1 }}
                disabled={!filter.active}
              />
            </Tooltip>
          )}
        </Box>

        <Box sx={OPERATION_STYLES.container}>
          <Button
            variant="contained"
            color="primary"
            onClick={onApplyOperation}
            startIcon={<PlayArrowIcon fontSize="small" />}
            disabled={!hasValidFilters}
            size="small"
            sx={OPERATION_STYLES.submitButton}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

export default Operations;
