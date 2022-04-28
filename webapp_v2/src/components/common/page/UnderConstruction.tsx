/* eslint-disable react-hooks/exhaustive-deps */
import ConstructionIcon from "@mui/icons-material/Construction";
import NoContent from "./NoContent";

function UnderConstruction() {
  return (
    <NoContent
      icon={<ConstructionIcon sx={{ width: "100px", height: "100px" }} />}
      title="main:underConstruction"
    />
  );
}

export default UnderConstruction;
