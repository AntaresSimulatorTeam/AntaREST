import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: 0,
  backgroundColor: "green",
}));

export const LinkContainer = styled(Box, {
  shouldForwardProp: (prop) => prop !== "multiple",
})<{ multiple?: boolean }>(({ theme, multiple }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItem: multiple === true ? "center" : "flex-end",
  marginBottom: multiple === true ? 0 : theme.spacing(2),
  boxSizing: "border-box",
  backgroundColor: "lightblue",
}));

export default {};
