import { Box, Tabs, styled } from "@mui/material";

export const TermsList = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  flexDirection: "column",
  marginBottom: theme.spacing(1),
}));

export const TermsHeader = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
  marginBottom: theme.spacing(2),
}));

export const MatrixContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  width: "100%",
  height: 650,
}));

export const StyledTab = styled(Tabs)({
  width: "100%",
  borderBottom: 1,
  borderColor: "divider",
});
