import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  flex: 1,
  flexFlow: "column nowrap",
  boxSizing: "border-box",
}));

export const Content = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "flex-start",
}));
