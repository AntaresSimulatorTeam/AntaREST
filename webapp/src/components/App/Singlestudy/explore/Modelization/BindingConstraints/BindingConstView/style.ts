import { Box, styled } from "@mui/material";

export const TermsList = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  flexDirection: "column",
  marginBottom: theme.spacing(1),
}));

export const TermsHeader = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  gap: 15,
  alignItems: "center",
  justifyContent: "flex-end",
  marginBottom: theme.spacing(1),
}));
