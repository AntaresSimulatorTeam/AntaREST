import { Box } from "@mui/material";
import SwaggerUI from "swagger-ui-react";
import "swagger-ui-react/swagger-ui.css";
import { getConfig } from "../../services/config";

function Api() {
  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const title = document.querySelector("title");
  if (title) {
    title.textContent = "Antares Web";
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      width="100%"
      height="100%"
      display="flex"
      flexDirection="column"
      alignItems="center"
      boxSizing="border-box"
      overflow="auto"
      sx={{ backgroundColor: "#eee" }}
    >
      <Box sx={{ zIndex: 999 }}>
        <SwaggerUI
          url={`${getConfig().baseUrl}${getConfig().restEndpoint}/openapi.json`}
        />
      </Box>
    </Box>
  );
}

export default Api;
