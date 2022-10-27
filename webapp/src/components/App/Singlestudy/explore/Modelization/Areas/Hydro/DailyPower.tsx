import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";

function DailyPower() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const creditModulationUrl = `input/hydro/common/capacity/creditmodulations_${areaId}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Credit modulation"
        study={study}
        url={creditModulationUrl}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default DailyPower;
