import { Box, Button, styled } from "@mui/material";

export const Code = styled(Box)({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-start",
  padding: "8px",
  overflow: "auto",
});

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
