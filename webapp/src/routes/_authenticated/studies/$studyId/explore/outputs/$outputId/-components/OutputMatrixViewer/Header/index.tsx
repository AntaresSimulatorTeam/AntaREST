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
import { Box, IconButton, Stack, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import useOutput from "../../../-hooks/useOutput";
import useOutputContext from "../../../-hooks/useOutputFilters";
import { createOutputDataPath } from "../../../-utils";
import { buildVariableViewParams } from "../utils";
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
    isMatrixDataLoaded,
    matrixGridRef,
  } = useOutputContext();
  const study = useStudy();
  const output = useOutput();

  const isVariablePerVariable = monteCarloMode === "variable-per-variable";

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleToggleDataFilter = () => {
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
          <Stack spacing={1}>
            <Tooltip title={t("matrix.filter.filterData")}>
              <IconButton onClick={handleToggleDataFilter} disabled={!isMatrixDataLoaded}>
                <FilterListIcon />
              </IconButton>
            </Tooltip>
            {isVariablePerVariable ? (
              <DownloadVariableViewButton
                params={buildVariableViewParams({ item, dataType, frequency, clusterId, variable })}
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
    </>
  );
}

export default Header;
