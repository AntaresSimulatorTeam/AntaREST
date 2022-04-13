import { NavLink } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import { styled } from "@mui/material";
import { DRAWER_WIDTH, DRAWER_WIDTH_EXTENDED } from "../theme";

export const NavExternalLink = styled("a")({
  color: "white",
  width: "100%",
  height: "100%",
  display: "flex",
  padding: 0,
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
  boxSizing: "border-box",
  textDecoration: 0,
  outline: 0,
});

export const NavListItem = styled(ListItem, {
  shouldForwardProp: (prop) => prop !== "link",
})<{ link?: boolean; extended?: boolean }>(({ theme, link }) => ({
  cursor: "pointer",
  width: "100%",
  height: "60px",
  padding: 0,
  margin: theme.spacing(1, 0),
  boxSizing: "border-box",
  "&:hover": {
    backgroundColor: theme.palette.primary.outlinedHoverBackground,
  },
  ...(!link && {
    display: "flex",
    flexFlow: "row nowrap",
    justifyContent: "flex-start",
    alignItems: "center",
  }),
}));

export const NavInternalLink = styled(NavLink)({
  width: "100%",
  height: "100%",
  display: "flex",
  padding: 0,
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
  boxSizing: "border-box",
  textDecoration: 0,
  outline: 0,
});

export const NavListItemText = styled(ListItemText)(({ theme }) => ({
  color: theme.palette.grey[400],
  "& span, & svg": {
    fontSize: "0.8em",
  },
}));

export const NavListItemIcon = styled(ListItemIcon)({
  width: "auto",
  display: "flex",
  boxSizing: "border-box",
  justifyContent: "center",
});

const options = {
  shouldForwardProp: (propName: PropertyKey) => propName !== "extended",
};

export const NavDrawer = styled(
  Drawer,
  options
)<{ extended?: boolean }>(({ extended }) => ({
  width: extended ? DRAWER_WIDTH_EXTENDED : DRAWER_WIDTH,
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: extended ? DRAWER_WIDTH_EXTENDED : DRAWER_WIDTH,
    boxSizing: "border-box",
    overflow: "hidden",
    backgroundColor: "inherit",
  },
}));

export default {};
