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
  type SelectChangeEvent,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { useTranslation } from "react-i18next";
import type { ColumnFilterProps } from "./types";
import { FILTER_TYPES } from "./constants";
import { useFilterControls } from "./hooks/useFilterControls";
import RangeFilterControl from "./components/RangeFilterControl";
import ListFilterControl from "./components/ListFilterControl";

const ColumnFilter = ({ filter, setFilter, columnCount }: ColumnFilterProps) => {
  const { t } = useTranslation();
  const {
    inputValue,
    handleListChange,
    addValueToList,
    removeValueFromList,
    clearAllValues,
    handleKeyPress,
    handleTypeChange,
  } = useFilterControls({ filter, setFilter });

  const handleTypeChangeEvent = (e: SelectChangeEvent) => {
    handleTypeChange(e.target.value);
  };

  const handleRangeChange = (newValues: [number, number]) => {
    setFilter({
      ...filter,
      columnsFilter: {
        ...filter.columnsFilter,
        range: {
          min: newValues[0],
          max: newValues[1],
        },
      },
    });
  };

  return (
    <Accordion defaultExpanded sx={{ mb: 1 }}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon fontSize="small" />}
        sx={{ py: 0, my: 0, maxHeight: 35, minHeight: 0 }}
      >
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500 }}>
          {t("matrix.filter.columnsFilter")}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0.5, pb: 1 }}>
        <FormControl fullWidth size="small" sx={{ mb: 1 }}>
          <InputLabel sx={{ fontSize: "0.8rem" }}>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.columnsFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChangeEvent}
            sx={{ fontSize: "0.8rem" }}
          >
            <MenuItem value={FILTER_TYPES.RANGE} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.filter.range")}
            </MenuItem>
            <MenuItem value={FILTER_TYPES.LIST} sx={{ fontSize: "0.8rem" }}>
              {t("matrix.filter.list")}
            </MenuItem>
          </Select>
        </FormControl>

        {filter.columnsFilter.type === FILTER_TYPES.RANGE && (
          <RangeFilterControl
            min={filter.columnsFilter.range?.min || 1}
            max={filter.columnsFilter.range?.max || columnCount}
            value={[
              filter.columnsFilter.range?.min || 1,
              filter.columnsFilter.range?.max || columnCount,
            ]}
            onChange={handleRangeChange}
            minBound={1}
            maxBound={columnCount || 100}
          />
        )}

        {filter.columnsFilter.type === FILTER_TYPES.LIST && (
          <ListFilterControl
            inputValue={inputValue}
            selectedValues={filter.columnsFilter.list || []}
            onInputChange={handleListChange}
            onKeyPress={handleKeyPress}
            onAddValue={() => addValueToList()}
            onRemoveValue={(value) => removeValueFromList(value)}
            onClearAll={() => clearAllValues()}
          />
        )}
      </AccordionDetails>
    </Accordion>
  );
};

export default ColumnFilter;
