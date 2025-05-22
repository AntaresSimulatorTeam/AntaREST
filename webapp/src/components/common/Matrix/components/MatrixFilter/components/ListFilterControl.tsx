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

import { TextField, Box, Typography, Stack, Chip, InputAdornment, IconButton } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import { useTranslation } from "react-i18next";

interface ListFilterControlProps {
  inputValue: string;
  selectedValues: number[];
  onInputChange: (value: string) => void;
  onKeyPress: (event: React.KeyboardEvent) => void;
  onAddValue: () => void;
  onRemoveValue: (value: number) => void;
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
                  <AddIcon />
                </IconButton>
              </InputAdornment>
            ),
          },
        }}
        helperText={t("matrix.filter.pressEnterOrComma")}
      />
      {selectedValues.length > 0 && (
        <Box sx={{ mt: 1 }}>
          <Typography variant="caption" display="block" gutterBottom>
            {t("matrix.filter.selectedValues")}:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {selectedValues.map((value) => (
              <Chip
                key={value}
                label={value}
                size="small"
                color="primary"
                onDelete={() => onRemoveValue(value)}
                sx={{ m: 0.5 }}
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
