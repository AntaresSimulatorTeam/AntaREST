import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../common/types";
import MatrixInput from "../../../../common/MatrixInput";

function Solar() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/solar/series/solar_${currentArea}`;

  return <MatrixInput study={study} url={url} />;
}

export default Solar;
