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

import { Typography, Paper, Grid, Box, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { SelectionSummaryProps } from "./types";

function SelectionSummary({ filteredData, previewMode = false }: SelectionSummaryProps) {
  const { t } = useTranslation();
  const theme = useTheme();

  const totalCells = filteredData.rowsIndices.length * filteredData.columnsIndices.length;

  return (
    <Paper
      variant="outlined"
      sx={{
        mt: 2,
        p: 2,
        backgroundColor: "background.paper",
        position: "relative",
        ...(previewMode && {
          boxShadow: "0 0 0 1px rgba(33, 150, 243, 0.2)",
          borderColor: "rgba(33, 150, 243, 0.3)",
        }),
      }}
    >
      {previewMode && (
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "2px",
            height: "100%",
            bgcolor: "info.main",
            opacity: 0.7,
          }}
        />
      )}
      <Typography
        variant="subtitle2"
        color={previewMode ? "info.main" : "primary.main"}
        gutterBottom
      >
        {t("matrix.filter.selectionSummary")}
      </Typography>

      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            {t("matrix.filter.selectedRows")}:
          </Typography>
          <Typography
            variant="h6"
            color={previewMode ? "info.main" : undefined}
            fontWeight={previewMode ? "medium" : "medium"}
            sx={previewMode ? { opacity: 0.9 } : undefined}
          >
            {filteredData.rowsIndices.length}
          </Typography>
        </Grid>

        <Grid item xs={6}>
          <Typography variant="body2" color="text.secondary">
            {t("matrix.filter.selectedColumns")}:
          </Typography>
          <Typography
            variant="h6"
            color={previewMode ? "info.main" : undefined}
            fontWeight={previewMode ? "medium" : "medium"}
            sx={previewMode ? { opacity: 0.9 } : undefined}
          >
            {filteredData.columnsIndices.length}
          </Typography>
        </Grid>

        <Grid item xs={12}>
          <Typography variant="body2" color="text.secondary">
            {t("matrix.filter.selectedCells")}:
          </Typography>
          <Typography
            variant="h5"
            color={previewMode ? "info.main" : "primary.main"}
            fontWeight="medium"
            sx={
              previewMode
                ? {
                    borderBottom: "1px dashed rgba(33, 150, 243, 0.4)",
                    display: "inline-block",
                    pb: 0.5,
                  }
                : undefined
            }
          >
            {totalCells}
            {previewMode && (
              <Box
                component="span"
                sx={{
                  fontSize: "0.65rem",
                  ml: 1,
                  color: theme.palette.info.main,
                  opacity: 0.7,
                  fontWeight: "normal",
                  verticalAlign: "middle",
                }}
              >
                preview
              </Box>
            )}
          </Typography>
        </Grid>
      </Grid>
    </Paper>
  );
}

export default SelectionSummary;
