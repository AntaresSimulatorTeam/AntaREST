import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../redux/selectors";
import { StudyMetadata } from "../../../../../common/types";
import MatrixInput from "../../../../common/MatrixInput";

function Reserve() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/reserves/${currentArea}`;
  const colmunsNames = [
    "Primary Res. (draft)",
    "Strategic Res. (draft)",
    "Day Ahead",
  ];

  return <MatrixInput study={study} url={url} columnsNames={colmunsNames} />;
}

export default Reserve;
