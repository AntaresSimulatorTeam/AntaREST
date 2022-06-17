import { Box, Drawer, styled } from "@mui/material";

export const CommandDrawer = styled(Drawer)(({ theme }) => ({
  width: "50%",
  flexShrink: 0,
  "& .MuiDrawer-paper": {
    width: "50%",
    boxSizing: "border-box",
    overflow: "hidden",
  },
}));

export const TitleContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  width: "100%",
  height: "100%",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: theme.spacing(1, 0),
  flexDirection: "column",
  flexWrap: "nowrap",
  boxSizing: "border-box",
  color: "white",
}));

export default {};
