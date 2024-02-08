import { styled, Box, Paper } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  padding: theme.spacing(2),
  paddingTop: 0,
  marginTop: theme.spacing(1),
  display: "flex",
  overflowY: "auto",
}));

export const FormBox = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  padding: theme.spacing(2),
  overflow: "auto",
}));

export const FormPaper = styled(Paper)(() => ({
  backgroundImage:
    "linear-gradient(rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.05))",
}));
