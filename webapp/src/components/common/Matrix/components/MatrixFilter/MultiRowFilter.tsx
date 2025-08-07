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

import AddIcon from "@mui/icons-material/Add";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Box, Button, IconButton, Tooltip } from "@mui/material";
import { produce } from "immer";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { createDefaultRowFilter } from "./constants";
import RowFilter from "./RowFilter";
import { DESIGN_TOKENS, ICON_BUTTON_STYLES } from "./styles";
import type { RowFilterProps } from "./types";

function MultiRowFilter({ filter, setFilter, datesInfo, timeFrequency }: RowFilterProps) {
  const { t } = useTranslation();
  const [expandedFilters, setExpandedFilters] = useState<string[]>(
    filter.rowsFilters.map((rf) => rf.id),
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAddFilter = useCallback(() => {
    const newFilter = createDefaultRowFilter(
      filter.rowsFilters[0]?.range?.max || 100,
      timeFrequency,
    );

    setFilter(
      produce((draft) => {
        draft.rowsFilters.push(newFilter);
      }),
    );

    setExpandedFilters((prev) => [...prev, newFilter.id]);
  }, [filter.rowsFilters, timeFrequency, setFilter]);

  const handleRemoveFilter = useCallback(
    (id: string) => {
      // Don't remove if it's the last filter
      if (filter.rowsFilters.length <= 1) {
        return;
      }

      setFilter(
        produce((draft) => {
          draft.rowsFilters = draft.rowsFilters.filter((rf) => rf.id !== id);
        }),
      );

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

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {filter.rowsFilters.map((rowFilter) => (
        <Box key={rowFilter.id} sx={{ mb: DESIGN_TOKENS.spacing.lg }}>
          <RowFilter
            filter={filter}
            setFilter={setFilter}
            datesInfo={datesInfo}
            timeFrequency={timeFrequency}
            filterId={rowFilter.id}
            onRemoveFilter={handleRemoveFilter}
            expanded={expandedFilters.includes(rowFilter.id)}
            onToggleExpanded={handleToggleExpanded}
          />
        </Box>
      ))}

      <Box
        sx={{
          mb: DESIGN_TOKENS.spacing.lg,
          display: "flex",
          alignItems: "center",
          gap: DESIGN_TOKENS.spacing.sm,
        }}
      >
        <Tooltip
          title={allExpanded ? t("matrix.filter.collapseAll") : t("matrix.filter.expandAll")}
        >
          <IconButton
            onClick={handleToggleAll}
            size="small"
            color={allExpanded ? "primary" : "default"}
            sx={ICON_BUTTON_STYLES.small}
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
            fontSize: DESIGN_TOKENS.fontSize.xs,
          }}
        >
          {t("matrix.filter.addRowFilter")}
        </Button>
      </Box>
    </>
  );
}

export default MultiRowFilter;
