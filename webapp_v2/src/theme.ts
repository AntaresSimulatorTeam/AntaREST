import { createTheme } from '@mui/material/styles';

export const DRAWER_WIDTH = 60;
export const DRAWER_WIDTH_EXTENDED = 240;

const theme = createTheme({
  typography: {
    fontFamily: "'Inter', sans-serif",
  },
  palette: {
    primary: {
      dark: '#112446',
      main: '#070c32',
      light: '#00a3ca',
    },
    secondary: {
      main: '#ffd927',
      light: '#ffd927AA',
    },
  },
});

export default theme;
