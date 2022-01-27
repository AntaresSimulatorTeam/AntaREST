import { createTheme } from '@mui/material/styles';

export const DRAWER_WIDTH = 60;
export const DRAWER_WIDTH_EXTENDED = 240;

const theme = createTheme({
  typography: {
    fontFamily: "'Inter', sans-serif",
  },
  palette: {
    primary: {
      dark: '#222433',//'#212032',
      main: '#1b0c25',
      light: '#03b2ff',
    },
    secondary: {
      main: '#ffb801',
      light: '#ffb80122',
    },
  },
});
export default theme;
