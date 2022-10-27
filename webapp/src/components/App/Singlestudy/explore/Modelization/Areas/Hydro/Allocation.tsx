import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";

function Allocation() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const allocationUrl = `input/hydro/allocation/${areaId}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Allocation"
        study={study}
        url={allocationUrl}
        computStats={MatrixStats.STATS}
      />
    </Root>
  );
}

export default Allocation;
