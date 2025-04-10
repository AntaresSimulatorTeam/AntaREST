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
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useTranslation } from "react-i18next";
import type { OperationsProps } from "./types";
import { Operation } from "../../shared/constants";

function Operations({ filter, setFilter, onApplyOperation }: OperationsProps) {
  const { t } = useTranslation();

  const handleOperationTypeChange = (e: { target: { value: string } }) => {
    setFilter({
      ...filter,
      operation: {
        ...filter.operation,
        type: e.target.value,
      },
    });
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilter({
      ...filter,
      operation: {
        ...filter.operation,
        value: Number.parseFloat(e.target.value) || 0,
      },
    });
  };

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.operation")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.operationType")}</InputLabel>
          <Select
            value={filter.operation.type}
            label={t("matrix.filter.operationType")}
            onChange={handleOperationTypeChange}
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
          <TextField
            label={t("matrix.filter.value")}
            type="number"
            value={filter.operation.value}
            onChange={handleValueChange}
            fullWidth
            margin="dense"
          />
        )}

        <Box sx={{ mt: 2, display: "flex", justifyContent: "flex-end" }}>
          <Button
            variant="contained"
            color="primary"
            onClick={onApplyOperation}
            startIcon={<PlayArrowIcon />}
            disabled={!filter.active}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}

export default Operations;
