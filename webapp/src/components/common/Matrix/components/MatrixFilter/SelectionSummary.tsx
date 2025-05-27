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

import { Typography, Paper, Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { SelectionSummaryProps } from "./types";

function SelectionSummary({ filteredData, previewMode = false }: SelectionSummaryProps) {
  const { t } = useTranslation();

  const totalCells = filteredData.rowsIndices.length * filteredData.columnsIndices.length;

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 0.5,
        ...(previewMode && {
          boxShadow: "0 0 0 1px rgba(33, 150, 243, 0.2)",
          borderColor: "rgba(33, 150, 243, 0.3)",
        }),
      }}
    >
      <Typography
        variant="caption"
        color={previewMode ? "info.main" : "primary.main"}
        gutterBottom
        sx={{ display: "block", textAlign: "center" }}
      >
        {t("matrix.filter.selectionSummary")}
      </Typography>

      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Box sx={{ textAlign: "center", flex: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
            {t("matrix.filter.selectedRows")}
          </Typography>
          <Typography
            variant="caption"
            color={previewMode ? "info.main" : "text.primary"}
            fontWeight="medium"
            sx={{ display: "block", fontSize: "0.8rem" }}
          >
            {filteredData.rowsIndices.length}
          </Typography>
        </Box>

        <Box sx={{ textAlign: "center", flex: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
            {t("matrix.filter.selectedColumns")}
          </Typography>
          <Typography
            variant="caption"
            color={previewMode ? "info.main" : "text.primary"}
            fontWeight="medium"
            sx={{ display: "block", fontSize: "0.8rem" }}
          >
            {filteredData.columnsIndices.length}
          </Typography>
        </Box>

        <Box sx={{ textAlign: "center", flex: 1 }}>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.65rem" }}>
            {t("matrix.filter.selectedCells")}
          </Typography>
          <Typography
            variant="body2"
            color={previewMode ? "info.main" : "primary.main"}
            fontWeight="medium"
            sx={{ display: "block", fontSize: "0.8rem" }}
          >
            {totalCells}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
}

export default SelectionSummary;
