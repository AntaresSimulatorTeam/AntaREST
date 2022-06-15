import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "500px",
  height: "200px",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2),
  boxSizing: "border-box",
  overflowX: "hidden",
  overflowY: "auto",
}));

export const InputContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexDirection: "row",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
}));

export default {};
