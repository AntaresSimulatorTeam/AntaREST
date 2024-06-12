import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import { Root } from "./style";

function Reserve() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/reserves/${currentArea}`;
  const colmunsNames = [
    "Primary Res. (draft)",
    "Strategic Res. (draft)",
    "DSM",
    "Day Ahead",
  ];

  return (
    <Root>
      <MatrixInput
        study={study}
        url={url}
        columnsNames={colmunsNames}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default Reserve;
