import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import DocLink from "../../../../../../common/DocLink";
import TabWrapper from "../../../TabWrapper";
import { ACTIVE_WINDOWS_DOC_PATH } from "../../BindingConstraints/BindingConstView/utils";
import { Root } from "./style";

function Hydro() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(
    () => [
      {
        label: "Management options",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/management`,
      },
      {
        label: "Inflow structure",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/inflowstructure`,
      },
      {
        label: "Allocation",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/allocation`,
      },
      {
        label: "Daily Power",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/dailypower`,
      },
      {
        label: "Energy Credits",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/energycredits`,
      },
      {
        label: "Reservoir levels",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/reservoirlevels`,
      },
      {
        label: "Water values",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/watervalues`,
      },
      {
        label: "Hydro Storage",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/hydrostorage`,
      },
      {
        label: "Run of river",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/ror`,
      },
    ],
    [study]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <DocLink to={`${ACTIVE_WINDOWS_DOC_PATH}#hydro`} isAbsolute />
      <TabWrapper study={study} tabStyle="normal" tabList={tabList} />
    </Root>
  );
}

export default Hydro;
