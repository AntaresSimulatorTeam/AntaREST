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

import { Box, styled, Typography } from "@mui/material";
import type { Theme } from "@glideapps/glide-data-grid";

export const MatrixContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(1),
  overflow: "hidden",
}));

export const MatrixHeader = styled(Box)({
  width: "100%",
  display: "flex",
  flexWrap: "nowrap",
  alignItems: "center",
});

export const MatrixTitle = styled(Typography)({
  fontSize: 20,
  fontWeight: 400,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  flex: 1,
});

export const darkTheme: Theme = {
  accentColor: "rgba(255, 184, 0, 0.9)",
  accentLight: "rgba(255, 184, 0, 0.2)",
  accentFg: "#FFFFFF",
  textDark: "#FFFFFF",
  textMedium: "#C1C3D9",
  textLight: "#A1A5B9",
  textBubble: "#FFFFFF",
  bgIconHeader: "#1E1F2E",
  fgIconHeader: "#FFFFFF",
  textHeader: "#FFFFFF",
  textGroupHeader: "#C1C3D9",
  bgCell: "#262737", // main background color
  bgCellMedium: "#2E2F42",
  bgHeader: "#1E1F2E",
  bgHeaderHasFocus: "#2E2F42",
  bgHeaderHovered: "#333447",
  bgBubble: "#333447",
  bgBubbleSelected: "#3C3E57",
  bgSearchResult: "#6366F133",
  borderColor: "rgba(255, 255, 255, 0.12)",
  drilldownBorder: "rgba(255, 255, 255, 0.35)",
  linkColor: "#818CF8",
  headerFontStyle: "bold 11px",
  baseFontStyle: "13px",
  fontFamily: "Inter, sans-serif",
  editorFontSize: "13px",
  lineHeight: 1.5,
  textHeaderSelected: "#FFFFFF",
  cellHorizontalPadding: 8,
  cellVerticalPadding: 5,
  headerIconSize: 16,
  markerFontStyle: "normal",
};

export const readOnlyDarkTheme: Partial<Theme> = {
  bgCell: "#1A1C2A",
  bgCellMedium: "#22243A",
  textDark: "#FAF9F6",
  textMedium: "#808080",
  textLight: "#606060",
  accentColor: "#4A4C66",
  accentLight: "rgba(74, 76, 102, 0.2)",
  borderColor: "rgba(255, 255, 255, 0.08)",
  drilldownBorder: "rgba(255, 255, 255, 0.2)",
  headerFontStyle: "bold 11px",
};

export const aggregatesTheme: Partial<Theme> = {
  bgCell: "#3D3E5F",
  bgCellMedium: "#383A5C",
  textDark: "#FFFFFF",
  fontFamily: "Inter, sans-serif",
  baseFontStyle: "13px",
  editorFontSize: "13px",
  headerFontStyle: "bold 11px",
};
