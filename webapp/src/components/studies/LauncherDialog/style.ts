import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  minWidth: "100px",
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: theme.spacing(2),
  boxSizing: "border-box",
  overflow: "hidden",
}));

export default {};
