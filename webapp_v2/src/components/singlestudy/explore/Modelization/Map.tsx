/* eslint-disable react-hooks/exhaustive-deps */
import { useOutletContext } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import { StudyMetadata } from "../../../../common/types";

function Map() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  return (
    <Box
      width="100%"
      flexGrow={1}
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      boxSizing="border-box"
      overflow="hidden"
    >
      <Typography my={2} variant="h5" color="primary">
        {" "}
        MAP: <br /> {study?.id}
      </Typography>
    </Box>
  );
}

export default Map;
