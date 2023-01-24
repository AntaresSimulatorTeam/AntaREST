import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import { MatrixStats, StudyMetadata } from "../../../../../../common/types";
import MatrixInput from "../../../../../common/MatrixInput";
import { Root } from "./style";
import DocLink from "../../../../../common/DocLink";
import { ACTIVE_WINDOWS_DOC_PATH } from "../BindingConstraints/BindingConstView/utils";

function Wind() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const currentArea = useAppSelector(getCurrentAreaId);
  const url = `input/wind/series/wind_${currentArea}`;

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <DocLink
        to={`${ACTIVE_WINDOWS_DOC_PATH}#wind`}
        isAbsolute
        sx={{ m: 0 }}
      />
      <MatrixInput study={study} url={url} computStats={MatrixStats.STATS} />
    </Root>
  );
}

export default Wind;
