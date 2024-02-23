import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";
import { MATRICES, HydroMatrixType } from "./utils";

interface Props {
  type: HydroMatrixType;
}

function HydroMatrix({ type }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  const hydroMatrix = MATRICES[type];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title={hydroMatrix.title}
        columnsNames={hydroMatrix.cols}
        rowNames={hydroMatrix.rows}
        study={study}
        url={hydroMatrix.url.replace("{areaId}", areaId)}
        computStats={hydroMatrix.stats}
        fetchFn={hydroMatrix.fetchFn}
        disableEdit={hydroMatrix.disableEdit}
        enablePercentDisplay={hydroMatrix.enablePercentDisplay}
        stretch={hydroMatrix.stretch}
      />
    </Root>
  );
}

export default HydroMatrix;
