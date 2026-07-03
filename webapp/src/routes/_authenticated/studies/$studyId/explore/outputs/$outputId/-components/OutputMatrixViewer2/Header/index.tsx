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
import CustomScrollbar from "@/components/CustomScrollbar";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import FilterListIcon from "@mui/icons-material/FilterList";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import { Box, IconButton, Stack, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useToggle } from "react-use";
import useOutputFilters from "../../../-hooks/useOutputFilters";
import ColumnsFilter from "./ColumnsFIlter";
import ResultFilters from "./ResultFilters";

interface Props {
  outputDataPath: string;
}

function Header({ outputDataPath }: Props) {
  const { t } = useTranslation();
  const { columnsSearch, matrixGridRef } = useOutputFilters();
  const [openColumnsFilter, toggleColumnsFilter] = useToggle(false);
  const study = useStudy();

  const isColumnsFilterActive =
    columnsSearch.variables.length > 0 ||
    columnsSearch.units.length > 0 ||
    columnsSearch.stats.length > 0;

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
        <CustomScrollbar>
          <Stack spacing={1} justifyContent="space-between" sx={{ py: 1 }}>
            <ResultFilters />
            <Stack spacing={0.5}>
              <Tooltip title="Filter columns">
                <IconButton
                  onClick={toggleColumnsFilter}
                  color={isColumnsFilterActive ? "secondary" : "default"}
                >
                  <ViewColumnIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title={t("matrix.filter.filterData")}>
                <IconButton onClick={handleToggleColumnsFilter}>
                  <FilterListIcon />
                </IconButton>
              </Tooltip>
              <DownloadMatrixButton studyId={study.id} path={outputDataPath} />
            </Stack>
          </Stack>
        </CustomScrollbar>
      </Box>
      <ColumnsFilter open={openColumnsFilter} onClose={toggleColumnsFilter} />
    </>
  );
}

export default Header;
