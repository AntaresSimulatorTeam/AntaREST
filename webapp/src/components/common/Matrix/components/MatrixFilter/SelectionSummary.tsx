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

import { Box, Paper, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { SELECTION_SUMMARY_STYLES } from "./styles";
import type { SelectionSummaryProps } from "./types";

function SelectionSummary({ filteredData }: SelectionSummaryProps) {
  const { t } = useTranslation();

  const totalCells = filteredData.rowsIndices.length * filteredData.columnsIndices.length;

  return (
    <Paper variant="outlined" sx={SELECTION_SUMMARY_STYLES.container}>
      <Box sx={SELECTION_SUMMARY_STYLES.statsContainer}>
        <Box sx={SELECTION_SUMMARY_STYLES.statItem}>
          <Typography variant="caption" color="text.secondary" sx={SELECTION_SUMMARY_STYLES.label}>
            {t("matrix.filter.selectedRows")}
          </Typography>
          <Typography variant="caption" fontWeight="medium" sx={SELECTION_SUMMARY_STYLES.value}>
            {filteredData.rowsIndices.length}
          </Typography>
        </Box>

        <Box sx={SELECTION_SUMMARY_STYLES.statItem}>
          <Typography variant="caption" color="text.secondary" sx={SELECTION_SUMMARY_STYLES.label}>
            {t("matrix.filter.selectedColumns")}
          </Typography>
          <Typography variant="caption" fontWeight="medium" sx={SELECTION_SUMMARY_STYLES.value}>
            {filteredData.columnsIndices.length}
          </Typography>
        </Box>

        <Box sx={SELECTION_SUMMARY_STYLES.statItem}>
          <Typography variant="caption" color="text.secondary" sx={SELECTION_SUMMARY_STYLES.label}>
            {t("matrix.filter.selectedCells")}
          </Typography>
          <Typography variant="body2" fontWeight="medium" sx={SELECTION_SUMMARY_STYLES.value}>
            {totalCells}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
}

export default SelectionSummary;
