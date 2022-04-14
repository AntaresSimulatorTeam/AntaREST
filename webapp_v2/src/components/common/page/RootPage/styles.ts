import { Box, experimental_sx as sx, styled, Typography } from "@mui/material";

export const HeaderTop = styled(Box)(
  sx({
    display: "flex",
    alignItems: "center",
    mb: 1,
  })
);

export const TitleWrapper = styled(Box)({
  display: "flex",
  alignItems: "center",
  flex: 1,
});

export const Title = styled(Typography)(sx({ ml: 2, fontSize: 34 }));

export const HeaderTopRight = styled(Box)({
  display: "flex",
  justifyContent: "flex-end",
  flex: 1,
});

export const HeaderBottom = styled(Box)(sx({ width: 1, mb: 1 }));
