/* eslint-disable react-hooks/exhaustive-deps */
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import logo from "../../../assets/logo.png";
import topRightBackground from "../../../assets/top-right-background.png";

function AppLoader() {
  const [t] = useTranslation();
  const [value, setValue] = useState<number>(0);
  const maxValue = 4;
  const timeDelay = 300;

  useEffect(() => {
    const interval = setInterval(() => {
      setValue((val) => (val + 1) % maxValue);
    }, timeDelay);
    return () => {
      if (interval) clearInterval(interval);
    };
  }, []);

  return (
    <Box
      display="flex"
      height="100vh"
      sx={{
        background:
          "linear-gradient(140deg, rgba(33,32,50,1) 0%, rgba(29,28,48,1) 35%, rgba(27,11,36,1) 100%)",
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
          width="400px"
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
            <img src={logo} alt="logo" style={{ height: "96px" }} />
            <Typography variant="h4" component="h4" color="primary" my={2}>
              Antares Web
            </Typography>
          </Box>
          <Typography sx={{ my: 3 }}>{`${t("main:loading")}${Array(value)
            .fill(0)
            .map((elm) => ".")
            .join("")}`}</Typography>
        </Box>
      </Box>
    </Box>
  );
}

export default AppLoader;
