import { styled, Box, Typography } from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";

export const BoxParamHeader = styled(Box)(({ theme }) => ({
  width: "100%",
  height: "40px",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  boxSizing: "border-box",
}));

export const BoxParam = styled(Box)(({ theme }) => ({
  flex: "1",
  width: "90%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  marginBottom: theme.spacing(2),
}));

export const ParamTitle = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.primary,
  marginRight: theme.spacing(1),
  fontWeight: "500",
}));

export const StyledDownloadIcon = styled(DownloadIcon)(({ theme }) => ({
  color: theme.palette.primary.main,
  marginLeft: theme.spacing(2),
  marginRight: theme.spacing(2),
  "&:hover": {
    color: theme.palette.primary.light,
  },
}));

export const StyledListingBox = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "flex-end",
  flexGrow: 1,
}));

export default {};
