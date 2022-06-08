import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../common/types";
import MatrixInput from "../../../../common/MatrixInput";

function Load() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/load/series/load_${currentArea}`;

  return <MatrixInput study={study} url={url} />;
}

export default Load;
