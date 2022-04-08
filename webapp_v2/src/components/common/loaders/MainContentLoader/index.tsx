import "./style.css";
import { Box } from "@mui/material";
import logo from "./logo.png";

function MainContentLoader() {
  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
    >
      <Box
        width="auto"
        height="auto"
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
      >
        <img
          src={logo}
          alt="logo"
          style={{
            width: "64px",
            height: "64px",
          }}
        />
        <div className="nest3" />
      </Box>
    </Box>
  );
}

export default MainContentLoader;
