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
  const { value, hasValidFilters, handleOperationTypeChange, handleValueChange } =
    useOperationControls({ filter, setFilter, onApplyOperation });

  const handleOperationTypeChangeEvent = (e: SelectChangeEvent<string>) => {
    handleOperationTypeChange(e.target.value);
  };

  const handleValueChangeEvent = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = Number.parseFloat(e.target.value) || 0;
    handleValueChange(newValue);
  };

  return (
    <Accordion defaultExpanded sx={{ my: 1, borderTop: "none" }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500 }}>
          {t("matrix.filter.operation")}
        </Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth size="small" sx={{ mb: 1 }}>
          <InputLabel sx={{ fontSize: "0.8rem" }}>{t("matrix.filter.operationType")}</InputLabel>
          <Select
            value={filter.operation.type}
            label={t("matrix.filter.operationType")}
            onChange={handleOperationTypeChangeEvent}
            disabled={!filter.active}
            sx={{ fontSize: "0.8rem" }}
          >
            <MenuItem value={Operation.Eq} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.equal")}
            </MenuItem>
            <MenuItem value={Operation.Add} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.add")}
            </MenuItem>
            <MenuItem value={Operation.Sub} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.subtract")}
            </MenuItem>
            <MenuItem value={Operation.Mul} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.multiply")}
            </MenuItem>
            <MenuItem value={Operation.Div} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.divide")}
            </MenuItem>
            <MenuItem value={Operation.Abs} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.operation.absolute")}
            </MenuItem>
          </Select>
        </FormControl>

        {filter.operation.type !== Operation.Abs && (
          <TextField
            label={t("matrix.filter.value")}
            type="number"
            value={value}
            onChange={handleValueChangeEvent}
            fullWidth
            size="small"
            sx={{ mb: 1, "& .MuiInputBase-input": { fontSize: "0.8rem" } }}
            disabled={!filter.active}
          />
        )}

        <Box sx={{ mt: 1, display: "flex", justifyContent: "flex-end" }}>
          <Button
            variant="contained"
            color="primary"
            onClick={onApplyOperation}
            startIcon={<PlayArrowIcon fontSize="small" />}
            disabled={!hasValidFilters}
            size="small"
            sx={{ fontSize: "0.6rem", py: 0.5 }}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

export default Operations;
