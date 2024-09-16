import { styled } from "@mui/material";

export const Flex = styled("div")(({ theme }) => ({
  height: "100%",
  display: "flex",
  flexDirection: "column",
  gap: theme.spacing(1),
}));

export const Menubar = styled("div")(({ theme }) => ({
  display: "flex",
  justifyContent: "flex-end",
  alignItems: "center",
  gap: theme.spacing(1),
}));

export const Filename = styled((props: { children?: string }) => (
  <div title={props.children} {...props} />
))({
  flex: 1,
  overflow: "hidden",
  textOverflow: "ellipsis",
});
