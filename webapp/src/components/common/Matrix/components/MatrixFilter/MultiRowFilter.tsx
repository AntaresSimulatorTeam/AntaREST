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

import { Box, Button, IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useCallback, useState, useMemo } from "react";
import AddIcon from "@mui/icons-material/Add";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
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
  const [expandedFilters, setExpandedFilters] = useState<string[]>(
    filter.rowsFilters.map((rf) => rf.id),
  );

  const handleAddFilter = useCallback(() => {
    const newFilter = createDefaultRowFilter(
      filter.rowsFilters[0]?.range?.max || 100,
      timeFrequency,
    );

    setFilter((prevFilter) => ({
      ...prevFilter,
      rowsFilters: [...prevFilter.rowsFilters, newFilter],
    }));

    setExpandedFilters((prev) => [...prev, newFilter.id]);
  }, [filter.rowsFilters, timeFrequency, setFilter]);

  const handleRemoveFilter = useCallback(
    (id: string) => {
      // Don't remove if it's the last filter
      if (filter.rowsFilters.length <= 1) {
        return;
      }

      setFilter((prevFilter) => ({
        ...prevFilter,
        rowsFilters: prevFilter.rowsFilters.filter((rf) => rf.id !== id),
      }));

      // Remove the ID from expanded filters
      setExpandedFilters((prev) => prev.filter((filterId) => filterId !== id));
    },
    [filter.rowsFilters.length, setFilter],
  );

  const handleToggleExpanded = useCallback((id: string) => {
    setExpandedFilters((prev) =>
      prev.includes(id) ? prev.filter((filterId) => filterId !== id) : [...prev, id],
    );
  }, []);

  const handleToggleAll = useCallback(() => {
    setExpandedFilters((prev) => {
      if (prev.length === filter.rowsFilters.length) {
        // If all are expanded, collapse all
        return [];
      }

      // Otherwise expand all
      return filter.rowsFilters.map((rf) => rf.id);
    });
  }, [filter.rowsFilters]);

  const allExpanded = useMemo(
    () => expandedFilters.length === filter.rowsFilters.length,
    [expandedFilters.length, filter.rowsFilters.length],
  );

  return (
    <>
      {filter.rowsFilters.map((rowFilter) => (
        <Box key={rowFilter.id} sx={{ mb: 1 }}>
          <RowFilter
            filter={filter}
            setFilter={setFilter}
            dateTime={dateTime}
            isTimeSeries={isTimeSeries}
            timeFrequency={timeFrequency}
            filterId={rowFilter.id}
            onRemoveFilter={handleRemoveFilter}
            expanded={expandedFilters.includes(rowFilter.id)}
            onToggleExpanded={handleToggleExpanded}
          />
        </Box>
      ))}

      <Box sx={{ display: "flex", gap: 1 }}>
        <Tooltip
          title={allExpanded ? t("matrix.filter.collapseAll") : t("matrix.filter.expandAll")}
        >
          <IconButton
            onClick={handleToggleAll}
            size="small"
            color={allExpanded ? "primary" : "default"}
            sx={{ p: 0.5 }}
          >
            {allExpanded ? (
              <ExpandLessIcon fontSize="small" />
            ) : (
              <ExpandMoreIcon fontSize="small" />
            )}
          </IconButton>
        </Tooltip>
        <Button
          startIcon={<AddIcon fontSize="small" />}
          onClick={handleAddFilter}
          variant="outlined"
          size="small"
          sx={{
            flex: 1,
            fontSize: "0.7rem",
          }}
        >
          {t("matrix.filter.addRowFilter")}
        </Button>
      </Box>
    </>
  );
}

export default MultiRowFilter;
