import SplitView from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

function InflowStructure() {
  return (
    <SplitView direction="horizontal" sizes={[50, 50]}>
      <HydroMatrix type={HydroMatrixType.InflowPattern} />
      <HydroMatrix type={HydroMatrixType.OverallMonthlyHydro} />
    </SplitView>
  );
}

export default InflowStructure;
