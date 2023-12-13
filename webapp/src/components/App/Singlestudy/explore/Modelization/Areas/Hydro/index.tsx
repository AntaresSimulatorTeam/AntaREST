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

  const tabList = useMemo(
    () => [
      {
        label: "Management options",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/management`,
      },
      {
        label: "Inflow structure",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/inflowstructure`,
      },
      {
        label: "Allocation",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/allocation`,
      },
      {
        label: "Correlation",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/correlation`,
      },
      {
        label: "Daily Power",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/dailypower`,
      },
      {
        label: "Energy Credits",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/energycredits`,
      },
      {
        label: "Reservoir levels",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/reservoirlevels`,
      },
      {
        label: "Water values",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/watervalues`,
      },
      {
        label: "Hydro Storage",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/hydrostorage`,
      },
      {
        label: "Run of river",
        path: `/studies/${study?.id}/explore/modelization/area/${areaId}/hydro/ror`,
      },
    ],
    [areaId, study?.id],
  );

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
