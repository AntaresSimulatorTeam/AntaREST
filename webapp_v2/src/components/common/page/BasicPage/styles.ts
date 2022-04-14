import { Box, experimental_sx as sx, styled } from "@mui/material";

export const Root = styled(Box)(
  sx({
    height: 1,
    display: "flex",
    flexDirection: "column",
  })
);

export const Header = styled("div")(
  sx({
    width: 1,
    py: 2,
    px: 3,
  })
);
