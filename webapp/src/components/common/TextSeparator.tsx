import { SxProps, Theme, Divider, Typography, Box } from "@mui/material";

interface Props {
  text: string;
  rootStyle?: SxProps<Theme> | undefined;
  textStyle?: SxProps<Theme> | undefined;
}
function TextSeparator(props: Props) {
  const { text, rootStyle, textStyle } = props;
  return (
    <Box
      width="100%"
      display="flex"
      flexDirection="row"
      justifyContent="flex-start"
      alignItems="center"
      sx={rootStyle}
    >
      <Typography variant="caption" sx={{ my: 2, ...textStyle }}>
        {text}
      </Typography>
      <Divider
        sx={{
          bgcolor: "rgba(255, 255, 255, 0.09)",
          flexGrow: 1,
          ml: 1,
          height: "2px",
        }}
      />
    </Box>
  );
}

TextSeparator.defaultProps = {
  rootStyle: undefined,
  textStyle: undefined,
};

export default TextSeparator;
