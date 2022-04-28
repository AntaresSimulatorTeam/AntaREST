import { styled } from "@mui/material";

export const StyledForm = styled("form")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
}));

export const StyledInput = styled("input")(({ theme }) => ({
  width: "200px",
  margin: theme.spacing(0, 2),
}));

export default {};
