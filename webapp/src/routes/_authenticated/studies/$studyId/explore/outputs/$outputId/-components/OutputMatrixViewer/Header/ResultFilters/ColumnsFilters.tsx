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
import { Divider } from "@mui/material";
import * as R from "ramda";
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

const getStaticsArrayFromFilter = (stats: ColumnStatisticsFilter): ColumnStatistics[] => {
  return R.toPairs(stats)
    .filter(([_, value]) => value)
    .map(([key]) => key);
};

function ColumnsFilters() {
  const { monteCarloMode, setColumnsFilters, columnsFilters } = useOutputContext();
  const { t } = useTranslation();
  const [searches, setSearches] = useState(columnsFilters.searches);
  const [inputSearch, setInputSearch] = useState("");
  const [stats, setStats] = useState<ColumnStatistics[]>(() =>
    getStaticsArrayFromFilter(columnsFilters.stats),
  );
  const isStatsEnabled = isMonteCarloModeHasStats(monteCarloMode);

  // Update columns filters when a field changes
  useUpdateEffect(() => {
    setColumnsFilters({
      searches: inputSearch ? [...searches, inputSearch] : searches,
      stats: COLUMN_STATISTICS.reduce((acc, stat) => {
        acc[stat] = stats.includes(stat);
        return acc;
      }, {} as ColumnStatisticsFilter),
    });
  }, [inputSearch, searches, stats, setColumnsFilters]);

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
          onChange={(event) => setStats(event.target.value)}
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
