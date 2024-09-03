import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import Matrix from "../../../../../common/MatrixGrid/Matrix";

function Load() {
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/load/series/load_${currentArea}`;

  return <Matrix url={url} />;
}

export default Load;
