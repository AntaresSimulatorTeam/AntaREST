import { useOutletContext } from "react-router";
import { MatrixStats, StudyMetadata } from "../../../../../../../common/types";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import MatrixInput from "../../../../../../common/MatrixInput";
import { Root } from "./style";

function EnergyCredits() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const standardCreditUrl = `input/hydro/common/capacity/maxpower_${areaId}`;

  const standardCreditCols = [
    "Generating Max Power(MW)",
    "Generating Max Energy(Hours at Pmax)",
    "Pumping Max Power(MW)",
    "Pumping Max Energy(Hours at Pmax)",
  ];

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <MatrixInput
        title="Standard credit"
        columnsNames={standardCreditCols}
        study={study}
        url={standardCreditUrl}
        computStats={MatrixStats.TOTAL}
      />
    </Root>
  );
}

export default EnergyCredits;
