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

import DownloadMatrixButton from "@/components/buttons/DownloadMatrixButton";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import FilterListIcon from "@mui/icons-material/FilterList";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import { Box, IconButton, Stack, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useToggle } from "react-use";
import useOutput from "../../../-hooks/useOutput";
import useOutputFilters from "../../../-hooks/useOutputFilters";
import { buildVariableViewParams, createOutputDataPath } from "../../../-utils";
import ColumnsFilter from "./ColumnsFIlter";
import DownloadVariableViewButton from "./DownloadVariableViewButton";
import ResultFilters from "./ResultFilters";

function Header() {
  const { t } = useTranslation();
  const {
    item,
    monteCarloMode,
    dataType,
    frequency,
    year,
    clusterId,
    variable,
    columnsSearch,
    isMatrixDataLoaded,
    matrixGridRef,
  } = useOutputFilters();
  const [openColumnsFilter, toggleColumnsFilter] = useToggle(false);
  const study = useStudy();
  const output = useOutput();

  const isColumnsFilterActive =
    columnsSearch.variables.length > 0 ||
    columnsSearch.units.length > 0 ||
    columnsSearch.stats.length > 0;

  const isVariablePerVariable = monteCarloMode === "variable-per-variable";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleToggleColumnsFilter = () => {
    matrixGridRef.current?.toggleFilter();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box>
        <Stack spacing={1} justifyContent="space-between">
          <ResultFilters />
          <Stack spacing={0.5}>
            {!isVariablePerVariable && (
              <Tooltip title="Filter columns">
                <IconButton
                  onClick={toggleColumnsFilter}
                  color={isColumnsFilterActive ? "secondary" : "default"}
                  disabled={!isMatrixDataLoaded}
                >
                  <ViewColumnIcon />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title={t("matrix.filter.filterData")}>
              <IconButton onClick={handleToggleColumnsFilter} disabled={!isMatrixDataLoaded}>
                <FilterListIcon />
              </IconButton>
            </Tooltip>
            {isVariablePerVariable ? (
              <DownloadVariableViewButton
                params={buildVariableViewParams(dataType, clusterId, item, variable, frequency)}
                disabled={!isMatrixDataLoaded}
              />
            ) : (
              <DownloadMatrixButton
                studyId={study.id}
                path={createOutputDataPath({
                  output,
                  item,
                  dataType,
                  frequency,
                  year,
                })}
                disabled={!isMatrixDataLoaded}
              />
            )}
          </Stack>
        </Stack>
      </Box>
      <ColumnsFilter open={openColumnsFilter} onClose={toggleColumnsFilter} />
    </>
  );
}

export default Header;
