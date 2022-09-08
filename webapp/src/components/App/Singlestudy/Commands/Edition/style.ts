import { Box, styled } from "@mui/material";

export const Root = styled(Box)(({ theme }) => ({
  flex: 1,
  height: "98%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  overflowY: "hidden",
}));

export const Header = styled(Box)(({ theme }) => ({
  width: "90%",
  height: "80px",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "space-between",
  alignItems: "center",
}));

export const EditHeader = styled(Box)(({ theme }) => ({
  flex: 1,
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-end",
  alignItems: "center",
}));

export const Body = styled(Box)(({ theme }) => ({
  width: "100%",
  maxHeight: "90%",
  minHeight: "90%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  overflow: "auto",
  boxSizing: "border-box",
  position: "relative",
  padding: theme.spacing(0, 2),
}));

export const headerIconStyle = {
  width: "24px",
  height: "auto",
  cursor: "pointer",
  color: "primary.main",
  mx: 2,
  "&:hover": {
    color: "primary.dark",
  },
};

export default {};
