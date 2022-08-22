import { Box, styled } from "@mui/material";

export const ConstraintList = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  flexDirection: "column",
  marginBottom: theme.spacing(1),
}));

export const ConstraintHeader = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
}));

export const ConstraintTerm = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  flexDirection: "column",
}));
