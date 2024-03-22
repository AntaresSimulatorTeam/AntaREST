import { Box, Paper, styled } from "@mui/material";

export const ConstraintElementRoot = styled(Paper)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(0.8),
  borderRadius: 5,
  backgroundImage:
    "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
}));

export const ConstraintElementData = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
}));
