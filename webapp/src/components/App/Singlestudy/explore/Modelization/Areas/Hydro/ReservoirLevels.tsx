import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";

function ReservoirLevels() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const reservoirLevelsUrl = `input/hydro/common/capacity/reservoir_${areaId}`;

  const reservoirLevelsCols = ["Lev Low(%)", "Lev Avg(%)", "Lev High(%)"];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Reservoir levels"
        columnsNames={reservoirLevelsCols}
        study={study}
        url={reservoirLevelsUrl}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default ReservoirLevels;
