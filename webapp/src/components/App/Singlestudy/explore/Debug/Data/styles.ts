import { styled } from "@mui/material";

export const Flex = styled("div")(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(1),
}));

export const Menubar = styled("div")({
  display: "flex",
  justifyContent: "flex-end",
});
