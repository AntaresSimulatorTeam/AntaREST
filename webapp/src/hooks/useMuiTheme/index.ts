import { PaletteMode, createTheme, useMediaQuery } from "@mui/material";
import { useMemo, useState } from "react";
import { deepmerge } from "@mui/utils";
import { baseTheme, darkPalette, lightPalette } from "./theme";

function useMuiTheme() {
  const prefersDarkMode = useMediaQuery("(prefers-color-scheme: dark)");
  const [themeMode, setThemeMode] = useState<PaletteMode>(
    prefersDarkMode ? "dark" : "light",
  );
  const theme = useMemo(() => {
    return createTheme(
      deepmerge(baseTheme, {
        palette: {
          ...(themeMode === "light" ? lightPalette : darkPalette),
          mode: themeMode,
        },
      }),
    );
  }, [themeMode]);

  return { theme, setThemeMode };
}

export default useMuiTheme;
