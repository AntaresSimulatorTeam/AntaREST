import SplitLayoutView from "../../../../../../common/SplitLayoutView";
import HydroMatrix from "./HydroMatrix";
import { MatrixType } from "./utils";

function InflowStructure() {
  return (
    <SplitLayoutView
      left={<HydroMatrix type={MatrixType.InflowPattern} />}
      right={<HydroMatrix type={MatrixType.OverallMonthlyHydro} />}
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
