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
  TextField,
  Box,
  Typography,
  Stack,
  Chip,
  InputAdornment,
  IconButton,
  Button,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ClearIcon from "@mui/icons-material/Clear";
import { useTranslation } from "react-i18next";

interface ListFilterControlProps {
  inputValue: string;
  selectedValues: number[];
  onInputChange: (value: string) => void;
  onKeyPress: (event: React.KeyboardEvent) => void;
  onAddValue: () => void;
  onRemoveValue: (value: number) => void;
  onClearAll?: () => void;
  placeholder?: string;
  disabled?: boolean;
}

const ListFilterControl = ({
  inputValue,
  selectedValues,
  onInputChange,
  onKeyPress,
  onAddValue,
  onRemoveValue,
  onClearAll,
  placeholder,
  disabled = false,
}: ListFilterControlProps) => {
  const { t } = useTranslation();

  return (
    <>
      <TextField
        label={t("matrix.filter.listValues")}
        placeholder={placeholder || t("matrix.filter.enterValue")}
        fullWidth
        margin="dense"
        value={inputValue}
        onChange={(e) => onInputChange(e.target.value)}
        onKeyDown={onKeyPress}
        type="number"
        disabled={disabled}
        sx={{
          "& .MuiInputBase-input": { fontSize: "0.8rem" },
          "& .MuiInputLabel-root": { fontSize: "0.8rem" },
          "& .MuiFormHelperText-root": { fontSize: "0.6rem" },
        }}
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={onAddValue}
                  disabled={!inputValue.trim() || disabled}
                  edge="end"
                  size="small"
                >
                  <AddIcon fontSize="small" />
                </IconButton>
              </InputAdornment>
            ),
          },
        }}
        helperText={t("matrix.filter.pressEnterOrComma")}
      />
      {selectedValues.length > 0 && (
        <Box sx={{ mt: 0.5 }}>
          <Box
            sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}
          >
            <Typography color="text.secondary" sx={{ fontSize: "0.6rem" }}>
              {t("matrix.filter.selectedValues")}:
            </Typography>
            {onClearAll && (
              <Button
                variant="text"
                size="small"
                startIcon={<ClearIcon fontSize="small" />}
                onClick={onClearAll}
                disabled={disabled}
                sx={{
                  minWidth: "auto",
                  fontSize: "0.6rem",
                  py: 0.2,
                  px: 0.5,
                  height: 20,
                }}
              >
                {t("matrix.filter.clearAll")}
              </Button>
            )}
          </Box>
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
            {selectedValues.map((value) => (
              <Chip
                key={value}
                label={value}
                size="small"
                color="primary"
                onDelete={() => onRemoveValue(value)}
                disabled={disabled}
              />
            ))}
          </Stack>
        </Box>
      )}
    </>
  );
};

export default ListFilterControl;
