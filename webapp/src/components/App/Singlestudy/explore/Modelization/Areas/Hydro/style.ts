import { styled, Box } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  padding: theme.spacing(2),
  display: "flex",
  overflow: "auto",
}));
