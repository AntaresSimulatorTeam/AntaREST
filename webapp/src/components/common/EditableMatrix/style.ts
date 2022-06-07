import { styled, Box, Button } from "@mui/material";
import { HotTable } from "@handsontable/react";
import { scrollbarStyle } from "../../../theme";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

export const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(180, 180, 180, 0.09)",
  color: "white",
  borderRight: "none !important",
  "&:hover": {
    color: "white",
    backgroundColor: theme.palette.secondary.main,
  },
  "&:disabled": {
    backgroundColor: theme.palette.secondary.dark,
    color: "white !important",
  },
}));

export const StyledHotTable = styled(HotTable)(() => ({
  "&> div > div": {
    ...scrollbarStyle,
  },
  backgroundColor: "#222333 !important",
  color: "white",
  borderColor: "rgba(255, 255, 255, 0.12) !important",
}));

export default {};
