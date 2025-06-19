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

import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  type SelectChangeEvent,
  TextField,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { Operation } from "../../shared/constants";
import { useOperationControls } from "./hooks/useOperationControls";
import { DESIGN_TOKENS, FORM_STYLES } from "./styles";
import type { OperationsProps } from "./types";

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
    <Box>
      <Box sx={{ ...FORM_STYLES.sideBySideContainer, mt: 3 }}>
        <Box sx={FORM_STYLES.responsiveContainer}>
          <FormControl size="small" sx={FORM_STYLES.sideBySideFormControl}>
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

          {filter.operation.type !== Operation.Abs && (
            <Box sx={{ flex: 1 }}>
              <TextField
                label={t("matrix.filter.value")}
                type="number"
                value={value}
                onChange={handleValueChangeEvent}
                size="small"
                sx={FORM_STYLES.textField}
                disabled={!filter.active}
              />
            </Box>
          )}

          <Button
            startIcon={<PlayArrowIcon fontSize="small" />}
            onClick={onApplyOperation}
            variant="outlined"
            size="small"
            disabled={!hasValidFilters}
            sx={{
              fontSize: DESIGN_TOKENS.fontSize.xs,
              alignSelf: "flex-end",
            }}
          >
            {t("matrix.filter.applyOperation")}
          </Button>
        </Box>
      </Box>
    </Box>
  );
}

export default Operations;
