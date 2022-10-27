import { useOutletContext } from "react-router";
import {
  MatrixStats,
  StudyMetadata,
} from "../../../../../../../../common/types";
import useAppSelector from "../../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../../common/MatrixInput";
import { Root } from "../style";

function HydroStorage() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const hydroStorageUrl = `input/hydro/series/${areaId}/mod`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Hydro Storage"
        study={study}
        url={hydroStorageUrl}
        computStats={MatrixStats.STATS}
      />
    </Root>
  );
}

export default HydroStorage;
