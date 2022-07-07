import { Box, ListItemButton, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(1, 2),
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
  padding: theme.spacing(0, 1),
}));

export const GroupButton = styled(ListItemButton)(({ theme }) => ({
  width: "100%",
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
  borderLeft: "4px solid black",
  borderColor: theme.palette.secondary.main,
  margin: theme.spacing(0.5, 0),
}));
