import { Box, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import ClusterRoot from "../common/ClusterRoot";
import ThermalView from "./ThermalView";

function Thermal() {
  const fixedGroupList = [
    "Gas",
    "Hard Coal",
    "Lignite",
    "Mixed fuel",
    "Nuclear",
    "Oil",
    "Other",
    "Other 2",
    "Other 3",
    "Other 4",
  ];
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  return (
    <ClusterRoot study={study} fixedGroupList={fixedGroupList} type="thermal">
      {({ cluster, groupList, nameList, back }) => (
        <Box
          sx={{
            width: "100%",
            height: "100%",
            bgcolor: "black",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Box sx={{ width: "100%", height: "80px" }}>
            <Button
              variant="text"
              color="secondary"
              onClick={back}
              startIcon={<ArrowBackIcon />}
            >
              Back to Cluster list
            </Button>
          </Box>
          <ThermalView
            study={study}
            cluster={cluster}
            groupList={groupList}
            nameList={nameList}
          />
        </Box>
      )}
    </ClusterRoot>
  );
}

export default Thermal;
