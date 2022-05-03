import { Box, List, styled } from "@mui/material";
import AddCircleOutlinedIcon from "@mui/icons-material/AddCircleOutlined";

export const Root = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "column nowrap",
  justifyContent: "flex-start",
  alignItems: "flex-start",
  padding: 0,
  marginBottom: 0,
  backgroundColor: "red",
}));

export const InputContainer = styled(Box)(({ theme }) => ({
  width: "100%",
  display: "flex",
  flexFlow: "row nowrap",
  justifyContent: "flex-start",
  alignItems: "center",
  padding: 0,
  marginBottom: theme.spacing(1),
}));

export const TagContainer = styled(List)(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  width: "100%",
  border: 0,
  backgroundColor: "black",
  justifyContent: "flex-start",
  flexWrap: "wrap",
  listStyle: "none",
  padding: theme.spacing(0.5),
  margin: 0,
}));

export const AddIcon = styled(AddCircleOutlinedIcon)(({ theme }) => ({
  color: theme.palette.primary.main,
  margin: theme.spacing(0, 1),
  cursor: "pointer",
  "&:hover": {
    color: theme.palette.primary.dark,
  },
}));

export default {};
