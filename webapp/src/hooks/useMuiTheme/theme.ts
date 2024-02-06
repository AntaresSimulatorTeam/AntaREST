import { PaletteOptions, ThemeOptions } from "@mui/material";
import { amber, grey } from "@mui/material/colors";

const SECONDARY_MAIN_COLOR = "#00B2FF";

export const baseTheme: ThemeOptions = {
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        "&::-webkit-scrollbar": {
          width: "7px",
          height: "7px",
        },
        "&::-webkit-scrollbar-track": {
          boxShadow: "inset 0 0 6px rgba(0, 0, 0, 0.3)",
        },
        "&::-webkit-scrollbar-thumb": {
          backgroundColor: SECONDARY_MAIN_COLOR,
        },
      },
    },
    MuiAutocomplete: {
      defaultProps: {
        size: "small",
      },
    },
    MuiButton: {
      defaultProps: {
        size: "small",
      },
    },
    MuiInputBase: {
      defaultProps: {
        size: "small",
      },
    },
    MuiSvgIcon: {
      defaultProps: {
        fontSize: "small",
      },
    },
    MuiCheckbox: {
      defaultProps: {
        size: "small",
      },
    },
  },
};

export const lightPalette: PaletteOptions = {
  // palette values for light mode
  primary: amber,
  divider: amber[200],
  text: {
    primary: grey[900],
    secondary: grey[800],
  },
};

export const darkPalette: PaletteOptions = {
  //primary: "",
  //secondary?: PaletteColorOptions;
  //error?: PaletteColorOptions;
  //warning?: PaletteColorOptions;
  //info?: PaletteColorOptions;
  //success?: PaletteColorOptions;
  //mode?: PaletteMode;
  //tonalOffset?: PaletteTonalOffset;
  //contrastThreshold?: number;
  //common?: Partial<CommonColors>;
  //grey?: ColorPartial;
  //text?: Partial<TypeText>;
  //divider?: string;
  //action?: Partial<TypeAction>;
  //background?: Partial<TypeBackground>;
};
