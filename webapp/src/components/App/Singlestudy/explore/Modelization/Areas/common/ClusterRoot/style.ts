import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(0, 2),
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "60px",
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
}));

export const ListContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  flex: 1,
}));
