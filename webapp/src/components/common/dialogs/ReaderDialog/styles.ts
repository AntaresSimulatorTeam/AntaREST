import { Box, styled } from "@mui/material";

export const Code = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  padding: "8px",
  overflow: "auto",
}));
