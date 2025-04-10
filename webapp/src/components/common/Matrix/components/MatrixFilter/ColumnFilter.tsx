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
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import type { FilterSectionProps } from "./types";
import { FILTER_TYPES } from "./constants";

const ColumnFilter = ({ filter, setFilter }: FilterSectionProps) => {
  const { t } = useTranslation();

  const handleTypeChange = (e: React.ChangeEvent<{ value: unknown }>) => {
    setFilter({
      ...filter,
      columnsFilter: {
        ...filter.columnsFilter,
        type: e.target.value as string,
      },
    });
  };

  const handleRangeChange = (field: "min" | "max", value: string) => {
    setFilter({
      ...filter,
      columnsFilter: {
        ...filter.columnsFilter,
        range: {
          ...filter.columnsFilter.range,
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
      columnsFilter: {
        ...filter.columnsFilter,
        modulo: {
          ...filter.columnsFilter.modulo,
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
      columnsFilter: {
        ...filter.columnsFilter,
        list: values,
      },
    });
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
            <MenuItem value={FILTER_TYPES.MODULO}>{t("matrix.filter.modulo")}</MenuItem>
            <MenuItem value={FILTER_TYPES.LIST}>{t("matrix.filter.list")}</MenuItem>
          </Select>
        </FormControl>

        {filter.columnsFilter.type === FILTER_TYPES.RANGE && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.min")}
              type="number"
              value={filter.columnsFilter.range?.min || 1}
              onChange={(e) => handleRangeChange("min", e.target.value)}
              fullWidth
            />
            <TextField
              label={t("matrix.filter.max")}
              type="number"
              value={filter.columnsFilter.range?.max || 1}
              onChange={(e) => handleRangeChange("max", e.target.value)}
              fullWidth
            />
          </Box>
        )}

        {filter.columnsFilter.type === FILTER_TYPES.MODULO && (
          <Box sx={{ display: "flex", gap: 2, mt: 2 }}>
            <TextField
              label={t("matrix.filter.divisor")}
              type="number"
              value={filter.columnsFilter.modulo?.divisor || 1}
              onChange={(e) => handleModuloChange("divisor", e.target.value)}
              fullWidth
            />
            <TextField
              label={t("matrix.filter.remainder")}
              type="number"
              value={filter.columnsFilter.modulo?.remainder || 0}
              onChange={(e) => handleModuloChange("remainder", e.target.value)}
              fullWidth
            />
          </Box>
        )}

        {filter.columnsFilter.type === FILTER_TYPES.LIST && (
          <TextField
            label={t("matrix.filter.listValues")}
            placeholder="e.g., 1,3,5,7"
            fullWidth
            margin="dense"
            value={filter.columnsFilter.list?.join(",") || ""}
            onChange={(e) => handleListChange(e.target.value)}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default ColumnFilter;
