import { styled, Box, Paper } from "@mui/material";
import { scrollbarStyle } from "../../../../../../theme";

export const Root = styled(Box)(({ theme }) => ({
  flex: 1,
  height: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
  padding: theme.spacing(2),
}));

export const Content = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  boxSizing: "border-box",
  flex: 1,
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  overflow: "auto",
  position: "relative",
  ...scrollbarStyle(theme.palette.secondary.main),
}));

export default {};
