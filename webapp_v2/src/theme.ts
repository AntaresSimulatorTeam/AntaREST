import * as React from "react";
import { createTheme } from "@mui/material/styles";

export const DRAWER_WIDTH = 60;
export const DRAWER_WIDTH_EXTENDED = 240;
export const STUDIES_HEIGHT_HEADER = 166;
export const STUDIES_SIDE_NAV_WIDTH = 300;
export const STUDIES_LIST_HEADER_HEIGHT = 100;
export const STUDIES_FILTER_WIDTH = 300;

export const scrollbarStyle = {
  "&::-webkit-scrollbar": {
    width: "7px",
    height: "7px",
  },
  "&::-webkit-scrollbar-track": {
    boxShadow: "inset 0 0 6px rgba(0, 0, 0, 0.3)",
  },
  "&::-webkit-scrollbar-thumb": {
    backgroundColor: "secondary.main",
    outline: "1px solid slategrey",
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
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: "#222333",
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
            "& .MuiOutlinedInput-root": {
              height: "50px",
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "rgba(255,255,255,0.09)",
              },
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
      main: "#00B2FF",
      light: "#77CFF5",
      contrast: "rgba(30, 30, 30, 0.87)",
      containedHoverBackground:
        "linear-gradient(0deg, rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), #00B2FF",
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
