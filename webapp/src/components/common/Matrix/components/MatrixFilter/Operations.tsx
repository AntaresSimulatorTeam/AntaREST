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
  Slider,
  type SelectChangeEvent,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useTranslation } from "react-i18next";
import type { OperationsProps } from "./types";
import { Operation } from "../../shared/constants";
import { useOperationControls } from "./hooks/useOperationControls";

function Operations({ filter, setFilter, onApplyOperation }: OperationsProps) {
  const { t } = useTranslation();
  const {
    value,
    quickOperations,
    hasValidFilters,
    handleOperationTypeChange,
    handleValueChange,
    handleSliderChange,
    applyQuickOperation,
  } = useOperationControls({ filter, setFilter, onApplyOperation });

  const handleOperationTypeChangeEvent = (e: SelectChangeEvent<string>) => {
    handleOperationTypeChange(e.target.value);
  };

  const handleValueChangeEvent = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number.parseFloat(e.target.value) || 0;
    handleValueChange(newValue);
  };

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.operation")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            {t("matrix.filter.quickOperations")}
          </Typography>
          <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
            {quickOperations.map((op) => (
              <Button
                key={op.label}
                variant="outlined"
                size="small"
                onClick={() => applyQuickOperation(op.op, op.value)}
                sx={{ minWidth: 40 }}
                disabled={!hasValidFilters}
              >
                {op.label}
              </Button>
            ))}
          </Box>
        </Box>

        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.operationType")}</InputLabel>
          <Select
            value={filter.operation.type}
            label={t("matrix.filter.operationType")}
            onChange={handleOperationTypeChangeEvent}
            disabled={!filter.active}
          >
            <MenuItem value={Operation.Eq}>{t("matrix.operation.equal")}</MenuItem>
            <MenuItem value={Operation.Add}>{t("matrix.operation.add")}</MenuItem>
            <MenuItem value={Operation.Sub}>{t("matrix.operation.subtract")}</MenuItem>
            <MenuItem value={Operation.Mul}>{t("matrix.operation.multiply")}</MenuItem>
            <MenuItem value={Operation.Div}>{t("matrix.operation.divide")}</MenuItem>
            <MenuItem value={Operation.Abs}>{t("matrix.operation.absolute")}</MenuItem>
          </Select>
        </FormControl>

        {filter.operation.type !== Operation.Abs && (
          <>
            <TextField
              label={t("matrix.filter.value")}
              type="number"
              value={value}
              onChange={handleValueChangeEvent}
              fullWidth
              margin="dense"
              disabled={!filter.active}
            />

            {filter.operation.type !== Operation.Div && (
              <Box sx={{ px: 2, pt: 1, pb: 0 }}>
                <Slider
                  value={value}
                  onChange={handleSliderChange}
                  min={-100}
                  max={100}
                  step={0.1}
                  valueLabelDisplay="auto"
                  disabled={!filter.active}
                  marks={[
                    { value: -100, label: "-100 " },
                    { value: -50, label: "-50 " },
                    { value: 0, label: "0 " },
                    { value: 50, label: "50 " },
                    { value: 100, label: "100 " },
                  ]}
                />
              </Box>
            )}
          </>
        )}

        <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
          <Button
            variant="contained"
            color="primary"
            onClick={onApplyOperation}
            startIcon={<PlayArrowIcon />}
            disabled={!hasValidFilters}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

export default Operations;
