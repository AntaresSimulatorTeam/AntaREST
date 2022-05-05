import { Box, Typography, TextField, Button, styled } from "@mui/material";

export const Fields = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "center",
  width: "100%",
  flexWrap: "wrap",
  marginBottom: theme.spacing(2),
  "&> div": {
    width: "270px",
    marginRight: theme.spacing(2),
  },
}));

export const SelectFields = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  width: "270px",
}));

export const Title = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.primary,
  fontSize: "1.25rem",
  fontWeight: 400,
  lineHeight: 1.334,
}));

export const StyledTextField = styled(TextField)(() => ({
  minHeight: 0,
  background: "rgba(255, 255, 255, 0.09)",
  borderRadius: "4px 4px 0px 0px",
  borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
}));

export const HoverButton = styled(Button)(({ theme }) => ({
  color: theme.palette.action.active,
  borderColor: theme.palette.text.disabled,
  "&:hover": {
    backgroundColor: "rgba(255,255,255,0.11)",
    borderColor: theme.palette.text.primary,
    color: theme.palette.text.primary,
  },
}));

export const ActiveButton = styled(Button)(({ theme }) => ({
  backgroundColor: "rgba(255,255,255,0.09) !important",
  color: `${theme.palette.text.primary} !important`,
  borderColor: `${theme.palette.text.secondary} !important`,
}));
export default {};
