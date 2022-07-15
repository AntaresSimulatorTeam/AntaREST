import { Box, ListItemButton, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "calc(100% - 50px)",
  boxSizing: "border-box",
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(1),
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
  display: "flex",
  flexFlow: "column nowrap",
  boxSizing: "border-box",
  padding: theme.spacing(1),
  overflow: "hidden",
}));

export const GroupButton = styled(ListItemButton)(({ theme }) => ({
  width: "100%",
  height: "auto",
  marginBottom: theme.spacing(1),
  borderWidth: "1px",
  borderRadius: "4px",
  borderStyle: "solid",
  borderLeftWidth: "4px",
  borderColor: theme.palette.divider,
  borderLeftColor: theme.palette.primary.main,
}));

export const ClusterButton = styled(ListItemButton)(({ theme }) => ({
  paddingLeft: theme.spacing(4),
  margin: theme.spacing(0.5, 0),
  height: "auto",
}));
