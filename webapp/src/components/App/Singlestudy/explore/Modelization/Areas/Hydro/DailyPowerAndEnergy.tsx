import SplitView from "../../../../../../common/SplitView";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

function DailyPowerAndEnergy() {
  return (
    <SplitView direction="vertical" sizes={[25, 75]}>
      <HydroMatrix type={HydroMatrixType.Dailypower} />
      <HydroMatrix type={HydroMatrixType.EnergyCredits} />
    </SplitView>
  );
}

export default DailyPowerAndEnergy;
