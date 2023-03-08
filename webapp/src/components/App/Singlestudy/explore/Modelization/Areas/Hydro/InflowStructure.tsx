import HydroMatrix from "./HydroMatrix";
import { Root } from "./style";
import { MatrixType } from "./utils";

function InflowStructure() {
  return (
    <Root sx={{ flexDirection: "column" }}>
      <HydroMatrix type={MatrixType.InflowPattern} />
      <HydroMatrix type={MatrixType.OverallMonthlyHydro} />
    </Root>
  );
}

export default InflowStructure;
