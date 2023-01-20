import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import { Root } from "./style";
import DocLink from "../../../../../common/DocLink";

function Solar() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/solar/series/solar_${currentArea}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <DocLink to="solar" isAbsolute />
      <MatrixInput study={study} url={url} computStats={MatrixStats.STATS} />
    </Root>
  );
}

export default Solar;
