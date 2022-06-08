import { styled, Box, Paper, Button } from "@mui/material";
import { scrollbarStyle } from "../../../theme";

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
  padding: theme.spacing(0, 2),
}));

export const Content = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  boxSizing: "border-box",
  flex: 1,
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  overflow: "auto",
  position: "relative",
  ...scrollbarStyle,
}));

export const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(180, 180, 180, 0.09)",
  color: "white",
  borderRight: "none !important",
  "&:hover": {
    color: "white",
    backgroundColor: theme.palette.secondary.main,
  },
  "&:disabled": {
    backgroundColor: theme.palette.secondary.dark,
    color: "white !important",
  },
}));
