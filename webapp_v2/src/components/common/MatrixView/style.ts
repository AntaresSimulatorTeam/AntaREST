import { styled, Box, Button } from "@mui/material";
import { HotTable } from "@handsontable/react";
import { scrollbarStyle } from "../../../theme";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  flexGrow: 1,
}));

export const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(0, 0, 0, 0.3)",
  color: "white",
  "&:hover": {
    color: "white",
    backgroundColor: theme.palette.primary.main,
  },
  "&:disabled": {
    backgroundColor: theme.palette.primary.dark,
    color: "white !important",
  },
}));

export const StyledHotTable = styled(HotTable)(({ theme }) => ({
  "&> div > div": {
    ...scrollbarStyle,
  },
}));

export default {};
