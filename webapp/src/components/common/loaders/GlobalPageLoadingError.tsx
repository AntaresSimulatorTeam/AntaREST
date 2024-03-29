import { Box, Typography } from "@mui/material";
import topRightBackground from "../../../assets/img/top-right-background.png";

function GlobalPageLoadingError() {
  return (
    <Box
      display="flex"
      height="100vh"
      sx={{
        background:
          "radial-gradient(ellipse at top right, #190520 0%, #190520 30%, #222333 100%)",
      }}
    >
      <Box
        position="absolute"
        top="0px"
        right="0px"
        display="flex"
        justifyContent="center"
        alignItems="center"
        flexDirection="column"
        flexWrap="nowrap"
        boxSizing="border-box"
      >
        <img src={topRightBackground} alt="logo" style={{ height: "auto" }} />
      </Box>
      <Box
        flexGrow={1}
        display="flex"
        alignItems="center"
        justifyContent="center"
        zIndex={999}
      >
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          flexDirection="column"
        >
          <Box
            display="flex"
            width="100%"
            justifyContent="center"
            alignItems="center"
            flexDirection="column"
            flexWrap="nowrap"
            boxSizing="border-box"
          >
            <Typography variant="h4" component="h4" color="primary" my={2}>
              Oops, an unexpected error happened.
              <br />
              Please try to refresh the page.
            </Typography>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}

export default GlobalPageLoadingError;
