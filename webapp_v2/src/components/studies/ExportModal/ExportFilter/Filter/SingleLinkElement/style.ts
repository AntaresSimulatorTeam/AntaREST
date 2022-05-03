import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: 0,
}));

export const LinkFilter = styled(Box)(({ theme }) => ({
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
  padding: 0,
  flexGrow: 1,
  backgroundColor: "violet",
  overflow: "hidden",
}));

export default {};
