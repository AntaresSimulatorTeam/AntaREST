import { styled, Box, Button } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  flexGrow: 1,
}));

export const StyledButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(0, 0, 0, 0.3)",
  color: "white",
  "&:hover": {
    color: "white",
  },
  "&:disabled": {
    backgroundColor: theme.palette.secondary.dark,
    color: "white !important",
  },
}));

export default {};
