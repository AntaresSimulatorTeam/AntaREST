import { Box } from "@mui/material";
import { useState } from "react";
import ClusterListing from "../common/ClusterListing";
import { Cluster } from "../common/ClusterListing/utils";

function Renewables() {
  const fixedGroupList = [
    "Wind Onshore",
    "Wind Offshore",
    "Solar Thermal",
    "Solar PV",
    "Solar Rooftop",
    "Other RES 1",
    "Other RES 2",
    "Other RES 3",
    "Other RES 4",
  ];
  const [currentCluster, setCurrentCluster] = useState<Cluster>();
  return currentCluster === undefined ? (
    <ClusterListing
      fixedGroupList={fixedGroupList}
      onClusterClick={(cluster: Cluster) => setCurrentCluster(cluster)}
    />
  ) : (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        bgcolor: "black",
      }}
    >
      {currentCluster && <p>{currentCluster.name}</p>}
    </Box>
  );
}

export default Renewables;
