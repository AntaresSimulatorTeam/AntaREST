import { styled, Box, Button } from "@mui/material";
import { HotTable } from "@handsontable/react";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

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

export const StyledHotTable = styled(HotTable)(() => ({
  backgroundColor: "#222333 !important",
  color: "white",
  borderColor: "rgba(255, 255, 255, 0.12) !important",
  "& table th": {
    backgroundColor: "#222333 !important",
    color: "white !important",
    borderColor: "rgba(255, 255, 255, 0.12) !important",
  },
  "& thead th.ht__active_highlight": {
    backgroundColor: "#00B2FF !important",
  },
  "& .handsontableInput": {
    backgroundColor: "#333652",
    color: "#fff",
  },
  "& .handsontable .htDimmed": {
    color: "rgba(255, 255, 255, 0.75) !important",
    backgroundColor: "#1c1e2e !important",
  },
}));

export default {};
