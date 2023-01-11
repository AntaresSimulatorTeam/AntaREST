import { styled, Box } from "@mui/material";
import { HuePicker } from "react-color";
import DeleteIcon from "@mui/icons-material/Delete";

export const AreasContainer = styled(Box)(() => ({
  width: "100%",
  flexGrow: 1,
  flexShrink: 1,
  display: "flex",
  flexDirection: "column",
  justifyContent: "flex-start",
  alignItems: "center",
  overflowY: "auto",
}));

export const AreaHuePicker = styled(HuePicker)(({ theme }) => ({
  width: "90% !important",
  margin: theme.spacing(1),
}));

export const AreaColorPicker = styled(Box)(({ theme }) => ({
  "& > div > div:first-of-type": {
    backgroundColor: "rgba(0, 0, 0, 0.12) !important",
    boxShadow: "none !important",
  },
  "& > div > div:last-of-type > div": {
    width: "unset !important",
    height: "120px !important",
    maxWidth: "275px !important",
    fontFamily: '"Inter", sans-serif !important',
    boxShadow: "none",
    "& > div > input, > div > div > div > input": {
      backgroundColor: "rgba(0,0,0,0)",
      color: `${theme.palette.text.secondary} !important`,
    },
  },
}));

export const AreaDeleteIcon = styled(DeleteIcon)(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.error.light,
  "&:hover": {
    color: theme.palette.error.main,
  },
}));

export const AreaLinkRoot = styled("div")(() => ({
  width: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
}));

export const AreaLinkTitle = styled("div")(({ theme }) => ({
  width: "90%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  color: theme.palette.text.secondary,
  fontWeight: "bold",
}));

export const AreaLinkContainer = styled("div")(() => ({
  width: "90%",
  display: "flex",
  justifyContent: "flex-start",
  alignItems: "baseline",
  boxSizing: "border-box",
}));

export const AreaLinkLabel = styled("div")(({ theme }) => ({
  fontWeight: "bold",
  color: theme.palette.text.secondary,
}));

export const AreaLinkContent = styled("div")(({ theme }) => ({
  cursor: "pointer",
  color: theme.palette.text.secondary,
  padding: theme.spacing(1.5),
  fontSize: 18,
  "&:hover": {
    textDecoration: "underline",
    color: "white",
  },
}));
