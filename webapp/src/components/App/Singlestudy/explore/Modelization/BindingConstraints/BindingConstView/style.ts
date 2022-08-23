import { Box, Tabs, styled } from "@mui/material";

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

export const MatrixContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  width: "100%",
  height: "500px",
  paddingRight: theme.spacing(2),
  marginBottom: theme.spacing(6),
}));

export const StyledTab = styled(Tabs)({
  width: "100%",
  borderBottom: 1,
  borderColor: "divider",
});
