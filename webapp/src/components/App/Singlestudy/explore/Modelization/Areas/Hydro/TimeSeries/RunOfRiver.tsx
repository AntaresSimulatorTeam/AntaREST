import { useOutletContext } from "react-router";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../../common/MatrixInput";
import { Root } from "../style";

function RunOfRiver() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const runOfRiverUrl = `input/hydro/series/${areaId}/ror`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Run of the river"
        study={study}
        url={runOfRiverUrl}
        computStats={MatrixStats.STATS}
      />
    </Root>
  );
}

export default RunOfRiver;
