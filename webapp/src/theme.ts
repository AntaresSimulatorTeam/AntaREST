/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import * as React from "react";
import { createTheme } from "@mui/material/styles";

export const DRAWER_WIDTH = 60;
export const DRAWER_WIDTH_EXTENDED = 240;
export const STUDIES_HEIGHT_HEADER = 100;
export const STUDIES_SIDE_NAV_WIDTH = 300;
export const STUDIES_LIST_HEADER_HEIGHT = 100;
export const STUDIES_FILTER_WIDTH = 300;

export const SECONDARY_MAIN_COLOR = "#00B2FF";
export const PAPER_BACKGROUND_NO_TRANSPARENCY = "#212c38";

export const scrollbarStyle = {
  "&::-webkit-scrollbar": {
    width: "10px",
    height: "10px",
  },
  "&::-webkit-scrollbar-track": {
    boxShadow: "inset 0 0 6px rgba(0, 0, 0, 0.3)",
  },
  "&::-webkit-scrollbar-thumb": {
    backgroundColor: SECONDARY_MAIN_COLOR,
    borderRadius: "10px",
    border: "2px solid transparent",
    backgroundClip: "padding-box",
  },
  "&::-webkit-scrollbar-thumb:hover": {
    border: 0,
  },
};

declare module "@mui/material/styles" {
  interface PaletteColor {
    contrast?: string;
    containedHoverBackground?: string;
    outlinedHoverBackground?: string;
    outlinedRestingBackground?: string;
  }
  interface SimplePaletteColorOptions {
    contrast?: string;
    containedHoverBackground?: string;
    outlinedHoverBackground?: string;
    outlinedRestingBackground?: string;
  }

  interface PaletteOptions {
    outlineBorder: React.CSSProperties["color"];
    standardFieldLine: React.CSSProperties["color"];
    backdrop: React.CSSProperties["color"];
    activeRating: React.CSSProperties["color"];
    snackbar: React.CSSProperties["color"];
  }
}

const theme = createTheme({
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        div: {
          ...scrollbarStyle,
        },
        ul: {
          ...scrollbarStyle,
        },
        pre: {
          ...scrollbarStyle,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: "#222333",
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          backgroundColor: "#222333",
          color: "#FFFFFF",
        },
      },
    },
    MuiPopover: {
      styleOverrides: {
        paper: {
          ...scrollbarStyle,
        },
      },
    },
    MuiButton: {
      variants: [
        {
          props: { variant: "contained", color: "success" },
          style: {
            color: "#FFFFFF",
          },
        },
        {
          props: { variant: "contained", color: "error" },
          style: {
            color: "#FFFFFF",
          },
        },
      ],
    },
    MuiTextField: {
      variants: [
        {
          props: { variant: "outlined" },
          style: {
            margin: "8px",
            "& .MuiOutlinedInput-root:not(.MuiInputBase-multiline):not(.MuiAutocomplete-inputRoot) .MuiInputAdornment-sizeMedium + .MuiOutlinedInput-input":
              {
                // Default value: 'padding: 16.5px 14px'
                // Don't use 'padding' to support adornments left and right
                paddingTop: "13.5px",
                paddingBottom: "13.5px",
              },
          },
        },
        {
          props: { variant: "filled" },
          style: {
            ".MuiFilledInput-root": {
              background: "rgba(255, 255, 255, 0.09)",
              borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
            },
            borderRadius: "4px 4px 0px 0px",
            minHeight: 0,
          },
        },
      ],
    },
    MuiSelect: {
      variants: [
        {
          props: { variant: "filled" },
          style: {
            background: "rgba(255, 255, 255, 0.09)",
            borderRadius: "4px 4px 0px 0px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
            ".MuiSelect-icon": {
              backgroundColor: "#222333",
            },
          },
        },
      ],
    },
    MuiFormControl: {
      variants: [
        {
          props: { variant: "outlined" },
          style: {
            "> div > fieldset": {
              borderColor: "rgba(255,255,255,0.09)",
            },
          },
        },
      ],
    },
  },
  typography: {
    fontFamily: "'Inter', sans-serif",
  },
  palette: {
    background: {
      default: "#222333",
    },
    primary: {
      dark: "#C9940B",
      main: "#FFB800",
      light: "#FFDB7D",
      contrast: "rgba(0, 0, 0, 0.87)",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #FFB800",
      outlinedHoverBackground: "rgba(255, 184, 0, 0.08)",
      outlinedRestingBackground: "rgba(255, 184, 0, 0.05)",
    },
    secondary: {
      dark: "#0092D0",
      main: SECONDARY_MAIN_COLOR,
      light: "#77CFF5",
      contrast: "rgba(30, 30, 30, 0.87)",
      containedHoverBackground: `linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), ${SECONDARY_MAIN_COLOR}`,
      outlinedHoverBackground: "rgba(0, 178, 255, 0.08)",
      outlinedRestingBackground: "rgba(0, 178, 255, 0.5)",
    },
    success: {
      dark: "#388E3C",
      main: "#66BB6A",
      light: "#81C784",
      contrast: "#FFFFFF",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #66BB6A",
      outlinedHoverBackground: "rgba(102, 187, 106, 0.5)",
      outlinedRestingBackground: "rgba(102, 187, 106, 0.08)",
    },
    warning: {
      dark: "#F57C00",
      main: "#FF9800",
      light: "#FFB74D",
      contrast: "#FFFFFF",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #FF9800",
      outlinedHoverBackground: "rgba(255, 152, 0, 0.08)",
      outlinedRestingBackground: "rgba(255, 152, 0, 0.05)",
    },
    error: {
      dark: "#D32F2F",
      main: "#F44336",
      light: "#E57373",
      contrast: "#FFFFFF",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #F44336",
      outlinedHoverBackground: "rgba(244, 67, 54, 0.08)",
      outlinedRestingBackground: "rgba(244, 67, 54, 0.05)",
    },
    info: {
      dark: "#1976D2",
      main: "#2196F3",
      light: "#64B5F6",
      contrast: "#FFFFFF",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #2196F3",
      outlinedHoverBackground: "rgba(33, 150, 243, 0.08)",
      outlinedRestingBackground: "rgba(33, 150, 243, 0.05)",
    },
    text: {
      primary: "#FFFFFF",
      secondary: "rgba(255, 255, 255, 0.7)",
      disabled: "rgba(255, 255, 255, 0.5)",
    },
    action: {
      active: "rgba(255, 255, 255, 0.56)",
      hover: "rgba(255, 255, 255, 0.32)",
      selected: "rgba(255, 255, 255, 0.16)",
      disabled: "rgba(255, 255, 255, 0.3)",
      disabledBackground: "rgba(255, 255, 255, 0.12)",
      focus: "rgba(255, 255, 255, 0.12)",
    },
    divider: "rgba(255, 255, 255, 0.12)",
    outlineBorder: "#222333",
    standardFieldLine: "#222333",
    backdrop: "rgba(0, 0, 0, 0.5)",
    activeRating: "#FFB400",
    snackbar: "#FFFFFF",
  },
});

export default theme;
