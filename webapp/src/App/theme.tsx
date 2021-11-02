import { createMuiTheme } from '@material-ui/core';

export const TOOLBAR_HEIGHT = '48px';

export const jobStatusColors = {
  running: 'orange',
  pending: 'orange',
  success: 'green',
  failed: 'red',
};

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
    fontFamily: "'Inter', sans-serif",
  },
  palette: {
    primary: {
      dark: '#112446',
      main: '#002a5e',
      light: '#00a3ca',
    },
    secondary: {
      main: '#ff9800',
    },
  },
});
