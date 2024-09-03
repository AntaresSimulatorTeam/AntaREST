import styled from "@emotion/styled";
import { Box, Typography } from "@mui/material";

export const MatrixContainer = styled(Box)(() => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  overflow: "hidden",
}));

export const MatrixHeader = styled(Box)(() => ({
  width: "100%",
  display: "flex",
  flexFlow: "row wrap",
  justifyContent: "space-between",
  alignItems: "flex-end",
}));

export const MatrixTitle = styled(Typography)(() => ({
  fontSize: 20,
  fontWeight: 400,
  lineHeight: 1,
}));
