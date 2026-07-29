/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import SearchMultipleFE from "@/components/fieldEditors/SearchMultipleFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import Fieldset from "@/components/Fieldset";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import { Box, Button, Drawer, Toolbar, Typography } from "@mui/material";
import * as R from "ramda";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useOutputContext from "../../../-hooks/useOutputFilters";
import {
  COLUMN_STATISTICS,
  DEFAULT_COLUMNS_FILTERS,
  isMonteCarloModeHasStats,
  type ColumnStatistics,
  type ColumnStatisticsFilter,
} from "../utils";

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

const getStaticsArrayFromFilter = (stats: ColumnStatisticsFilter): ColumnStatistics[] => {
  return R.toPairs(stats)
    .filter(([_, value]) => value)
    .map(([key]) => key);
};

function ColumnsFilters({ open, onClose }: Props) {
  const { monteCarloMode, setColumnsFilters, columnsFilters } = useOutputContext();
  const { t } = useTranslation();
  const [searches, setSearches] = useState(columnsFilters.searches);
  const [inputSearch, setInputSearch] = useState("");
  const [stats, setStats] = useState<ColumnStatistics[]>(() =>
    getStaticsArrayFromFilter(columnsFilters.stats),
  );
  const isStatsEnabled = isMonteCarloModeHasStats(monteCarloMode);

  // Automatically submit the filters when a field changes
  useUpdateEffect(
    () => {
      handleSubmit();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [inputSearch, searches, stats],
  );

  ////////  ////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  function handleSubmit() {
    setColumnsFilters({
      searches: inputSearch ? [...searches, inputSearch] : searches,
      stats: COLUMN_STATISTICS.reduce((acc, stat) => {
        acc[stat] = stats.includes(stat);
        return acc;
      }, {} as ColumnStatisticsFilter),
    });
  }

  const handleReset = () => {
    setColumnsFilters(DEFAULT_COLUMNS_FILTERS);

    // Reset local state to default values
    setSearches(DEFAULT_COLUMNS_FILTERS.searches);
    setInputSearch("");
    setStats(getStaticsArrayFromFilter(DEFAULT_COLUMNS_FILTERS.stats));

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Drawer
      open={open}
      onClose={onClose}
      anchor="right"
      sx={{ left: "unset" }}
      slotProps={{
        paper: { sx: { width: 300 } },
        // hideBackdrop={true} removes the backdrop DOM element entirely,
        // eliminating the click target that triggers `onClose`.
        // Using transparent backdrop preserves the invisible click target
        // for pointer events while removing the visual overlay.
        backdrop: {
          sx: {
            backgroundColor: "transparent",
          },
        },
      }}
    >
      <Toolbar>
        <ViewColumnIcon sx={{ mr: 1 }} />
        <Typography variant="h6">{t("study.outputs.filterColumns")}</Typography>
      </Toolbar>

      <Box component="form" sx={{ px: 2, height: 1, overflow: "auto" }}>
        <Fieldset fullFieldWidth>
          <SearchMultipleFE
            value={searches}
            inputValue={inputSearch}
            onSearchValuesChange={setSearches}
            onInputValueChange={setInputSearch}
          />
          {isStatsEnabled && (
            <SelectFE
              label={t("study.outputs.statistics")}
              value={stats}
              options={COLUMN_STATISTICS}
              onChange={(event) => setStats(event.target.value)}
              multiple
            />
          )}
        </Fieldset>
      </Box>

      <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, p: 1 }}>
        <Button variant="outlined" onClick={handleReset}>
          {t("global.reset")}
        </Button>
        <Button variant="contained" onClick={onClose}>
          {t("global.close")}
        </Button>
      </Box>
    </Drawer>
  );
}

export default ColumnsFilters;
