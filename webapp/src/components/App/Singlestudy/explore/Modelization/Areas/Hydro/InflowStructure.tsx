import SplitLayoutView from "../../../../../../common/SplitLayoutView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

function InflowStructure() {
  return (
    <SplitLayoutView
      left={<HydroMatrix type={HydroMatrixType.InflowPattern} />}
      right={<HydroMatrix type={HydroMatrixType.OverallMonthlyHydro} />}
      sx={{
        ".SplitLayoutView__Left": {
          width: "50%",
        },
        ".SplitLayoutView__Right": {
          height: "100%",
        },
      }}
    />
  );
}

export default InflowStructure;
