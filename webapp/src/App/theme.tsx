import { createMuiTheme } from '@material-ui/core';

export const TOOLBAR_HEIGHT = '48px';

export default createMuiTheme({
  overrides: {
    MuiToolbar: {
      dense: {
        minHeight: TOOLBAR_HEIGHT,
      },
    },
    MuiCardContent: {
      root: {
        padding: '8px 16px',
      },
    },
  },
  typography: {
    fontFamily: "'Open Sans', sans-serif",
  },
  palette: {
    primary: {
      dark: '#112446',
      main: '#002a5e',
      light: '#00a3ca',
    },
    secondary: {
      main: '#ff9800',
    }
  },
});
