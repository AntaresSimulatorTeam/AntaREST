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

const darkColors = {
  base: "#141a26",
  header: "#161c2a",
  lighter: "#1b2331",
  lightest: "#212b3e",
  dateTimeBg: "#161c2a",
  text: "#ffffff",
  textMedium: "#c1c3d9",
  accent: "rgba(255, 184, 0, 0.9)",
  accentLight: "rgba(255, 184, 0, 0.2)",
  aggregateBg: "#464770",
  aggregateAvgBg: "#3d3e5f",
};

const lightColors = {
  base: "#ffffff",
  lighter: "#f5f5f5",
  lightest: "#eeeeee",
  header: "#e8e8e8",
  text: "#000000",
  textMedium: "#555555",
  accent: "rgba(25, 118, 210, 0.9)",
  accentLight: "rgba(25, 118, 210, 0.2)",
  dateTimeBg: "#e3e3e8",
  aggregateBg: "#ffe4e1",
  aggregateAvgBg: "#ffc4bc",
};

export const darkTheme: Theme = {
  accentColor: darkColors.accent,
  accentLight: darkColors.accentLight,
  accentFg: darkColors.text,
  textDark: darkColors.text,
  textMedium: darkColors.textMedium,
  textLight: "#a1a5b9",
  textBubble: darkColors.text,
  bgIconHeader: darkColors.header,
  fgIconHeader: darkColors.text,
  textHeader: darkColors.text,
  textGroupHeader: darkColors.textMedium,
  bgCell: darkColors.lighter,
  bgCellMedium: darkColors.lightest,
  bgHeader: darkColors.header,
  bgHeaderHasFocus: darkColors.lighter,
  bgHeaderHovered: darkColors.lightest,
  bgBubble: darkColors.lightest,
  bgBubbleSelected: "#2a365a",
  bgSearchResult: "#6366f133",
  borderColor: "rgba(255, 255, 255, 0.12)",
  drilldownBorder: "rgba(255, 255, 255, 0.35)",
  linkColor: "#818cf8",
  headerFontStyle: "bold 11px",
  baseFontStyle: "13px",
  fontFamily: "Inter, sans-serif",
  editorFontSize: "13px",
  lineHeight: 1.5,
  textHeaderSelected: darkColors.text,
  cellHorizontalPadding: 8,
  cellVerticalPadding: 5,
  headerIconSize: 16,
  markerFontStyle: "normal",
};

export const lightTheme: Theme = {
  ...darkTheme,
  accentColor: lightColors.accent,
  accentLight: lightColors.accentLight,
  accentFg: lightColors.text,
  textDark: lightColors.text,
  textMedium: lightColors.textMedium,
  textLight: "#777777",
  textBubble: lightColors.text,
  bgIconHeader: lightColors.header,
  fgIconHeader: lightColors.text,
  textHeader: lightColors.text,
  textGroupHeader: lightColors.textMedium,
  bgCell: lightColors.base,
  bgCellMedium: lightColors.lighter,
  bgHeader: lightColors.header,
  bgHeaderHasFocus: lightColors.lighter,
  bgHeaderHovered: lightColors.lightest,
  bgBubble: lightColors.lightest,
  bgBubbleSelected: "#e0e0e0",
  bgSearchResult: "#1976d233",
  borderColor: "rgba(0, 0, 0, 0.12)",
  drilldownBorder: "rgba(0, 0, 0, 0.35)",
  linkColor: "#1976d2",
};

export const readOnlyDarkTheme: Partial<Theme> = {
  bgCell: darkColors.header,
  bgCellMedium: darkColors.base,
  textDark: "#faf9f6",
  textMedium: "#808080",
  textLight: "#606060",
  accentColor: "#2a365a",
  accentLight: "rgba(42, 54, 90, 0.2)",
  borderColor: "rgba(255, 255, 255, 0.08)",
  drilldownBorder: "rgba(255, 255, 255, 0.2)",
};

export const readOnlyLightTheme: Partial<Theme> = {
  bgCell: lightColors.header,
  bgCellMedium: lightColors.lighter,
  textDark: lightColors.text,
  textMedium: "#666666",
  textLight: "#888888",
  accentColor: "#e0e0e0",
  accentLight: "rgba(224, 224, 224, 0.2)",
  borderColor: "rgba(0, 0, 0, 0.08)",
  drilldownBorder: "rgba(0, 0, 0, 0.2)",
};

export const dateTimeTheme = {
  dark: {
    bgCell: darkColors.dateTimeBg,
  },
  light: {
    bgCell: lightColors.dateTimeBg,
  },
};

export const aggregatesTheme = {
  dark: {
    bgCell: darkColors.aggregateBg,
    textDark: darkColors.text,
  },
  light: {
    bgCell: lightColors.aggregateBg,
    textDark: lightColors.text,
  },
};

export const aggregatesAvgTheme = {
  dark: {
    bgCell: darkColors.aggregateAvgBg,
    textDark: darkColors.text,
  },
  light: {
    bgCell: lightColors.aggregateAvgBg,
    textDark: lightColors.text,
  },
};
