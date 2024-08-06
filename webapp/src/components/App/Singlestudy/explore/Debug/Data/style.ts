import { styled, Box } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  flex: 1,
  height: "100%",
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(1, 1),
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "center",
  marginBottom: theme.spacing(1),
}));
