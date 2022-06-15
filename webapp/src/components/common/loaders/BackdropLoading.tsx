import { Backdrop, Box, CircularProgress } from "@mui/material";

interface BackdropLoadingProps {
  open: boolean;
  children?: React.ReactNode;
}

function BackdropLoading(props: BackdropLoadingProps) {
  const { open, children } = props;

  const Comp = (
    <Backdrop
      open={open}
      sx={{
        position: "absolute",
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <CircularProgress color="inherit" />
    </Backdrop>
  );

  if (children) {
    return (
      <Box sx={{ position: "relative" }}>
        {children}
        {Comp}
      </Box>
    );
  }

  return Comp;
}

export default BackdropLoading;
