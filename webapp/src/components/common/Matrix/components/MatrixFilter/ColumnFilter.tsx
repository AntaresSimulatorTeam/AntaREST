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
  Box,
  TextField,
  Chip,
  Stack,
  IconButton,
  InputAdornment,
  Slider,
  type SelectChangeEvent,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import { useState } from "react";
import type { ColumnFilterProps } from "./types";
import { FILTER_TYPES } from "./constants";

const ColumnFilter = ({ filter, setFilter, columnCount }: ColumnFilterProps) => {
  const { t } = useTranslation();

  const handleTypeChange = (e: SelectChangeEvent) => {
    setFilter({
      ...filter,
      columnsFilter: {
        ...filter.columnsFilter,
        type: e.target.value,
      },
    });
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    if (Array.isArray(newValue)) {
      setFilter({
        ...filter,
        columnsFilter: {
          ...filter.columnsFilter,
          range: {
            min: newValue[0],
            max: newValue[1],
          },
        },
      });
    }
  };

  const [inputValue, setInputValue] = useState<string>("");

  const handleListChange = (value: string) => {
    setInputValue(value);
  };

  const addValueToList = () => {
    const newValue = Number.parseInt(inputValue.trim());
    if (!Number.isNaN(newValue)) {
      // Only add if the value is not already in the list
      if (!filter.columnsFilter.list?.includes(newValue)) {
        setFilter({
          ...filter,
          columnsFilter: {
            ...filter.columnsFilter,
            list: [...(filter.columnsFilter.list || []), newValue].sort((a, b) => a - b),
          },
        });
      }
      // Clear the input field after adding
      setInputValue("");
    }
  };

  const removeValueFromList = (valueToRemove: number) => {
    setFilter({
      ...filter,
      columnsFilter: {
        ...filter.columnsFilter,
        list: (filter.columnsFilter.list || []).filter((value) => value !== valueToRemove),
      },
    });
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addValueToList();
    }
  };

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.columnsFilter")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.columnsFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChange}
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {filter.columnsFilter.type === FILTER_TYPES.RANGE && (
          <Box sx={{ px: 2, pt: 3, pb: 1 }}>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "flex", justifyContent: "space-between" }}
            >
              <span>{filter.columnsFilter.range?.min || 1}</span>
              <span>{filter.columnsFilter.range?.max || columnCount}</span>
            </Typography>
            <Slider
              value={[
                filter.columnsFilter.range?.min || 1,
                filter.columnsFilter.range?.max || columnCount,
              ]}
              onChange={handleSliderChange}
              valueLabelDisplay="auto"
              min={1}
              max={columnCount || 100}
              sx={{ mt: 1 }}
            />
          </Box>
        )}

        {filter.columnsFilter.type === FILTER_TYPES.LIST && (
          <>
            <TextField
              label={t("matrix.filter.listValues")}
              placeholder={t("matrix.filter.enterValue")}
              fullWidth
              margin="dense"
              value={inputValue}
              onChange={(e) => handleListChange(e.target.value)}
              onKeyDown={handleKeyPress}
              type="number"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={addValueToList}
                      disabled={!inputValue.trim()}
                      edge="end"
                      size="small"
                    >
                      <AddIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              helperText={t("matrix.filter.pressEnterOrComma")}
            />
            {(filter.columnsFilter.list?.length || 0) > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" display="block" gutterBottom>
                  {t("matrix.filter.selectedValues")}:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                  {filter.columnsFilter.list?.map((value) => (
                    <Chip
                      key={value}
                      label={value}
                      size="small"
                      color="primary"
                      onDelete={() => removeValueFromList(value)}
                      sx={{ m: 0.5 }}
                    />
                  ))}
                </Stack>
              </Box>
            )}
          </>
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default ColumnFilter;
