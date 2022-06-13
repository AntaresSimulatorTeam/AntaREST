import { Box, styled, Typography } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: theme.spacing(2),
  boxSizing: "border-box",
  overflowX: "hidden",
  overflowY: "auto",
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "50px",
  display: "flex",
  flexDirection: "row",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
}));

export const EditorContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  height: "calc(100% - 40px)",
  width: "100%",
  boxSizing: "border-box",
  overflow: "auto",
}));

export const EditorButton = styled(Typography)(({ theme }) => ({
  margin: theme.spacing(0, 2),
  fontSize: "1em",
  color: theme.palette.text.primary,
  cursor: "pointer",
  "&:hover": {
    color: theme.palette.secondary.main,
  },
}));

export const EditorIcon = {
  width: "20px",
  height: "auto",
  color: "text.primary",
  cursor: "pointer",
  my: 0,
  mx: 2,
  "&:hover": {
    color: "secondary.main",
  },
};

export default {};
