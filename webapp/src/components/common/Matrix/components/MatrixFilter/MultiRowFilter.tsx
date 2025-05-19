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

import { Box, Button, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import AddIcon from "@mui/icons-material/Add";
import RowFilter from "./RowFilter";
import { createDefaultRowFilter } from "./constants";
import type { RowFilterProps } from "./types";

function MultiRowFilter({
  filter,
  setFilter,
  dateTime,
  isTimeSeries,
  timeFrequency,
}: RowFilterProps) {
  const { t } = useTranslation();

  const handleAddFilter = () => {
    const newFilter = createDefaultRowFilter(
      filter.rowsFilters[0]?.range?.max || 100,
      timeFrequency,
    );
    setFilter({
      ...filter,
      rowsFilters: [...filter.rowsFilters, newFilter],
    });
  };

  const handleRemoveFilter = (id: string) => {
    // Don't remove if it's the last filter
    if (filter.rowsFilters.length <= 1) {
      return;
    }

    setFilter({
      ...filter,
      rowsFilters: filter.rowsFilters.filter((rf) => rf.id !== id),
    });
  };

  return (
    <Box>
      <Typography variant="subtitle1" gutterBottom sx={{ mb: 1 }}>
        {t("matrix.filter.rowsFilters")}
      </Typography>
      <Typography variant="caption" color="text.secondary" paragraph>
        {t("matrix.filter.rowsFiltersDescription")}
      </Typography>

      {filter.rowsFilters.map((rowFilter) => (
        <Box key={rowFilter.id} sx={{ mb: 2 }}>
          <RowFilter
            filter={filter}
            setFilter={setFilter}
            dateTime={dateTime}
            isTimeSeries={isTimeSeries}
            timeFrequency={timeFrequency}
            filterId={rowFilter.id}
            onRemoveFilter={handleRemoveFilter}
          />
        </Box>
      ))}

      <Box sx={{ mt: 2, mb: 2 }}>
        <Button
          startIcon={<AddIcon />}
          onClick={handleAddFilter}
          variant="outlined"
          size="small"
          fullWidth
        >
          {t("matrix.filter.addRowFilter")}
        </Button>
      </Box>
    </Box>
  );
}

export default MultiRowFilter;
