import { Box, styled } from "@mui/material";
import { scrollbarStyle } from "../../../theme";

/*
Same style as Properties Dialog
will be replaced by 
*/

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2),
  boxSizing: "border-box",
  overflowX: "hidden",
  overflowY: "auto",
  ...scrollbarStyle,
}));

export const InputElement = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexDirection: "row",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
}));

export const ElementContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  boxSizing: "border-box",
}));

export default {};
