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
import SelectFE, { type SelectFEChangeEvent } from "@/components/fieldEditors/SelectFE";
import { Divider } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import useOutputContext from "../../../../-hooks/useOutputFilters";
import {
  COLUMN_STATISTICS,
  isMonteCarloModeHasStats,
  type ColumnStatistics,
  type ColumnStatisticsFilter,
} from "../../utils";

function ColumnsFilters() {
  const { monteCarloMode, setColumnsFilters, columnsFilters } = useOutputContext();
  const { t } = useTranslation();
  const [searches, setSearches] = useState(columnsFilters.searches);
  const [inputSearch, setInputSearch] = useState("");
  const stats = COLUMN_STATISTICS.filter((stat) => columnsFilters.stats[stat]);
  const isStatsEnabled = isMonteCarloModeHasStats(monteCarloMode);

  // Update columns filters when a search changes
  useUpdateEffect(() => {
    setColumnsFilters((prev) => ({
      ...prev,
      searches: inputSearch ? [...searches, inputSearch] : searches,
    }));
  }, [inputSearch, searches, setColumnsFilters]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleStatsChange = (event: SelectFEChangeEvent<ColumnStatistics[]>) => {
    const selectedStats = event.target.value;
    const newStats = COLUMN_STATISTICS.reduce((acc, stat) => {
      acc[stat] = selectedStats.includes(stat);
      return acc;
    }, {} as ColumnStatisticsFilter);

    setColumnsFilters((prev) => ({ ...prev, stats: newStats }));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SearchMultipleFE
        value={searches}
        inputValue={inputSearch}
        onSearchValuesChange={setSearches}
        onInputValueChange={setInputSearch}
        size="extra-small"
        sx={{ minWidth: 150 }}
      />
      {isStatsEnabled && (
        <SelectFE
          label={t("study.outputs.statistics")}
          value={stats}
          options={COLUMN_STATISTICS}
          onChange={handleStatsChange}
          multiple
          size="extra-small"
          sx={{ minWidth: 150 }}
        />
      )}
      <Divider flexItem orientation="vertical" variant="middle" />
    </>
  );
}

export default ColumnsFilters;
