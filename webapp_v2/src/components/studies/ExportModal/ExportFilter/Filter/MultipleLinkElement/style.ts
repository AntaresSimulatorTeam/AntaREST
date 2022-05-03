import { Box, List, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "center",
  alignItems: "center",
  padding: 0,
  backgroundColor: "green",
}));

export const FilterLinkContainer = styled(List)(({ theme }) => ({
  display: "flex",
  border: 0,
  backgroundColor: "#00000000",
  justifyContent: "center",
  flexWrap: "wrap",
  listStyle: "none",
  padding: theme.spacing(0.5),
  marginTop: theme.spacing(1),
  margin: 0,
}));

export default {};
