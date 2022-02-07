import { createTheme } from '@mui/material/styles';

export const DRAWER_WIDTH = 60;
export const DRAWER_WIDTH_EXTENDED = 240;
export const STUDIES_HEIGHT_HEADER = 150;
export const STUDIES_SIDE_NAV_WIDTH = 300;
export const STUDIES_LIST_HEADER_HEIGHT = 100;
export const STUDIES_FILTER_WIDTH = 300;

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
