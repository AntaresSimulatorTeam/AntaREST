import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import DocLink from "../../../../../../common/DocLink";
import TabWrapper from "../../../TabWrapper";
import { ACTIVE_WINDOWS_DOC_PATH } from "../../BindingConstraints/BindingConstView/utils";
import { Root } from "./style";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";

function Hydro() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  const tabList = useMemo(() => {
    const basePath = `/studies/${study?.id}/explore/modelization/area/${encodeURI(
      areaId,
    )}/hydro`;

    return [
      { label: "Management options", path: `${basePath}/management` },
      { label: "Inflow structure", path: `${basePath}/inflowstructure` },
      { label: "Allocation", path: `${basePath}/allocation` },
      { label: "Correlation", path: `${basePath}/correlation` },
      { label: "Daily Power", path: `${basePath}/dailypower` },
      { label: "Energy Credits", path: `${basePath}/energycredits` },
      { label: "Reservoir levels", path: `${basePath}/reservoirlevels` },
      { label: "Water values", path: `${basePath}/watervalues` },
      { label: "Hydro Storage", path: `${basePath}/hydrostorage` },
      { label: "Run of river", path: `${basePath}/ror` },
    ];
  }, [areaId, study?.id]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#hydro`} isAbsolute />
      <TabWrapper study={study} tabList={tabList} isScrollable />
    </Root>
  );
}

export default Hydro;
