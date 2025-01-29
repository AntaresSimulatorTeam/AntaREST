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

import { colors, type CssVarsThemeOptions, type Theme } from "@mui/material";

const TAB_MIN_HEIGHT = 38;

export default {
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
        backgroundColor: colors.lightBlue[500],
      },
    },
  },
  MuiFormControl: {
    defaultProps: {
      size: "small",
      margin: "dense", // Prevent label from being cut
    },
  },
  MuiAutocomplete: {
    defaultProps: {
      size: "small",
      slotProps: {
        paper: {
          sx: (theme: Theme) =>
            theme.applyStyles("light", { backgroundImage: theme.vars.overlays[0] }),
        },
      },
    },
  },
  MuiButton: {
    defaultProps: {
      size: "small",
    },
    styleOverrides: {
      root: {
        flexShrink: 0,
      },
    },
  },
  MuiToggleButton: {
    variants: [
      {
        props: { size: "extra-small" },
        style: {
          padding: 4,
        },
      },
    ],
  },
  MuiButtonGroup: {
    defaultProps: {
      size: "small",
    },
  },
  MuiToggleButtonGroup: {
    defaultProps: {
      size: "small",
    },
  },
  MuiCheckbox: {
    defaultProps: {
      size: "small",
    },
    variants: [
      {
        props: { size: "extra-small" },
        style: {
          padding: 6,
        },
      },
    ],
  },
  MuiInputBase: {
    defaultProps: {
      size: "small",
    },
    variants: [
      {
        props: { disabled: false },
        style: ({ theme }) =>
          theme.applyStyles("light", { backgroundColor: theme.palette.background.paper }),
      },
    ],
  },
  MuiInputLabel: {
    defaultProps: {
      shrink: true,
    },
  },
  MuiOutlinedInput: {
    defaultProps: {
      notched: true, // Fix for empty field with `shrink` to true
    },
  },
  MuiTextField: {
    variants: [
      {
        props: { size: "extra-small" },
        style: {
          margin: 0,
          ".MuiInputBase-root": {
            padding: "0 9px",
          },
          input: {
            padding: "4px 0",
          },
        },
      },
    ],
  },
  MuiSelect: {
    defaultProps: {
      MenuProps: {
        MenuListProps: {
          sx: (theme: Theme) =>
            theme.applyStyles("light", { backgroundColor: theme.palette.background.paper }),
        },
      },
    },
    variants: [
      {
        props: { size: "extra-small" },
        style: {
          ".MuiInputBase-input": {
            padding: "4px 30px 4px 10px",
          },
        },
      },
    ],
  },
  MuiSvgIcon: {
    defaultProps: {
      fontSize: "small",
    },
    variants: [
      {
        props: { fontSize: "extra-small" },
        style: {
          fontSize: "1rem",
        },
      },
    ],
  },
  MuiChip: {
    defaultProps: {
      size: "small",
    },
  },
  MuiTabs: {
    styleOverrides: {
      root: {
        minHeight: TAB_MIN_HEIGHT,
        // Add 2px like default MUI theme for bottom border when tab is selected
        height: `${TAB_MIN_HEIGHT + 2}px !important`,
      },
    },
  },
  MuiTab: {
    styleOverrides: {
      root: {
        paddingTop: 5,
        paddingBottom: 5,
        minHeight: TAB_MIN_HEIGHT,
      },
    },
  },
} satisfies CssVarsThemeOptions["components"];
