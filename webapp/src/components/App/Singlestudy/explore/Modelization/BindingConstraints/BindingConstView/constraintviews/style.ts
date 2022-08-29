import { Box, Paper, styled } from "@mui/material";
import { PAPER_BACKGROUND_NO_TRANSPARENCY } from "../../../../../../../../theme";

export const ConstraintElementRoot = styled(Paper)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  padding: theme.spacing(1),
  backgroundColor: PAPER_BACKGROUND_NO_TRANSPARENCY,
}));

export const ConstraintElementHeader = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
}));

export const ConstraintElementData = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
}));
