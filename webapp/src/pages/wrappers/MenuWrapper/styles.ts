import { NavLink } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";

import { Box, styled } from "@mui/material";
import {
  DRAWER_WIDTH,
  DRAWER_WIDTH_EXTENDED,
  scrollbarStyle,
} from "../../../theme";

export const Root = styled(Box)({
  display: "flex",
  width: "100vw",
  height: "100vh",
  overflow: "hidden",
  background:
    "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
});

export const TootlbarContent = styled(Box, {
  shouldForwardProp: (prop) => prop !== "extended",
})<{ extended?: boolean }>(({ extended }) => ({
  display: "flex",
  width: "100%",
  height: "100%",
  justifyContent: extended ? "flex-start" : "center",
  alignItems: "center",
  flexDirection: "row",
  flexWrap: "nowrap",
  boxSizing: "border-box",
}));

export const MenuContainer = styled(Box)({
  display: "flex",
  flex: 1,
  justifyContent: "space-between",
  flexDirection: "column",
  boxSizing: "border-box",
  overflowY: "auto",
  ...scrollbarStyle,
});

export const LogoContainer = styled(Box)({
  position: "absolute",
  top: "0px",
  right: "0px",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  flexFlow: "column nowrap",
  boxSizing: "border-box",
});

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
