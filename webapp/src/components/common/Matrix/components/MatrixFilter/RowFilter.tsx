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
  type SelectChangeEvent,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import type { FilterSectionProps } from "./types";
import { FILTER_TYPES, TIME_INDEXING } from "./constants";

function RowFilter({ filter, setFilter }: FilterSectionProps) {
  const { t } = useTranslation();

  const handleIndexingTypeChange = (e: SelectChangeEvent) => {
    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        indexingType: e.target.value,
      },
    });
  };

  const handleTypeChange = (e: SelectChangeEvent) => {
    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        type: e.target.value,
      },
    });
  };

  const handleRangeChange = (field: "min" | "max", value: string) => {
    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        range: {
          ...filter.rowsFilter.range,
          [field]: Number.parseInt(value) || 1,
        } as { min: number; max: number },
      },
    });
  };

  const handleModuloChange = (field: "divisor" | "remainder", value: string) => {
    const parsedValue =
      field === "divisor" ? Number.parseInt(value) || 1 : Number.parseInt(value) || 0;

    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        modulo: {
          ...filter.rowsFilter.modulo,
          [field]: parsedValue,
        } as { divisor: number; remainder: number },
      },
    });
  };

  const handleListChange = (value: string) => {
    const values = value
      .split(",")
      .map((val) => Number.parseInt(val.trim()))
      .filter((val) => !Number.isNaN(val));

    setFilter({
      ...filter,
      rowsFilter: {
        ...filter.rowsFilter,
        list: values,
      },
    });
  };

  return (
    <Accordion defaultExpanded>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{t("matrix.filter.rowsFilter")}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.indexingType")}</InputLabel>
          <Select
            value={filter.rowsFilter.indexingType}
            label={t("matrix.filter.indexingType")}
            onChange={handleIndexingTypeChange}
          >
            <MenuItem value={TIME_INDEXING.DAY_OF_MONTH}>
              {t("matrix.filter.indexing.dayOfMonth")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.DAY_OF_YEAR}>
              {t("matrix.filter.indexing.dayOfYear")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.DAY_HOUR}>
              {t("matrix.filter.indexing.dayHour")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.HOUR_YEAR}>
              {t("matrix.filter.indexing.hourYear")}
            </MenuItem>
            <MenuItem value={TIME_INDEXING.MONTH}>{t("matrix.filter.indexing.month")}</MenuItem>
            <MenuItem value={TIME_INDEXING.WEEK}>{t("matrix.filter.indexing.week")}</MenuItem>
            <MenuItem value={TIME_INDEXING.WEEKDAY}>{t("matrix.filter.indexing.weekday")}</MenuItem>
          </Select>
        </FormControl>

        <FormControl fullWidth margin="dense">
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.rowsFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChange}
          >
            <MenuItem value={FILTER_TYPES.RANGE}>{t("matrix.filter.range")}</MenuItem>
            <MenuItem value={FILTER_TYPES.MODULO}>{t("matrix.filter.modulo")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {filter.rowsFilter.type === FILTER_TYPES.RANGE && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.min")}
              type="number"
              value={filter.rowsFilter.range?.min || 1}
              onChange={(e) => handleRangeChange("min", e.target.value)}
              fullWidth
            />
            <TextField
              label={t("matrix.filter.max")}
              type="number"
              value={filter.rowsFilter.range?.max || 1}
              onChange={(e) => handleRangeChange("max", e.target.value)}
              fullWidth
            />
          </Box>
        )}

        {filter.rowsFilter.type === FILTER_TYPES.MODULO && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.divisor")}
              type="number"
              value={filter.rowsFilter.modulo?.divisor || 1}
              onChange={(e) => handleModuloChange("divisor", e.target.value)}
              fullWidth
            />
            <TextField
              label={t("matrix.filter.remainder")}
              type="number"
              value={filter.rowsFilter.modulo?.remainder || 0}
              onChange={(e) => handleModuloChange("remainder", e.target.value)}
              fullWidth
            />
          </Box>
        )}

        {filter.rowsFilter.type === FILTER_TYPES.LIST && (
          <TextField
            label={t("matrix.filter.listValues")}
            placeholder="e.g., 1,3,5,7"
            fullWidth
            margin="dense"
            value={filter.rowsFilter.list?.join(",") || ""}
            onChange={(e) => handleListChange(e.target.value)}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );
}

export default RowFilter;
