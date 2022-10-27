import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";

function WaterValues() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const waterValuesUrl = `input/hydro/common/capacity/waterValues_${areaId}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Water values"
        study={study}
        url={waterValuesUrl}
        computStats={MatrixStats.STATS}
      />
    </Root>
  );
}

export default WaterValues;
