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
import { FILTER_TYPES, type FilterType } from "./constants";
import { ACCORDION_STYLES, TYPOGRAPHY_STYLES, FORM_STYLES, DESIGN_TOKENS } from "./styles";
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
    handleTypeChange(e.target.value as FilterType);
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
    <Accordion defaultExpanded sx={ACCORDION_STYLES.marginBottom}>
      <AccordionSummary
        expandIcon={<ExpandMoreIcon fontSize="small" />}
        sx={ACCORDION_STYLES.summary}
      >
        <Typography sx={TYPOGRAPHY_STYLES.sectionTitle}>
          {t("matrix.filter.columnsFilter")}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={ACCORDION_STYLES.details}>
        <FormControl fullWidth size="small" sx={{ mb: DESIGN_TOKENS.spacing.lg }}>
          <InputLabel>{t("matrix.filter.type")}</InputLabel>
          <Select
            value={filter.columnsFilter.type}
            label={t("matrix.filter.type")}
            onChange={handleTypeChangeEvent}
            sx={FORM_STYLES.formControl}
          >
            <MenuItem value={FILTER_TYPES.RANGE} sx={FORM_STYLES.menuItem}>
              {t("matrix.filter.range")}
            </MenuItem>
            <MenuItem value={FILTER_TYPES.LIST} sx={FORM_STYLES.menuItem}>
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
