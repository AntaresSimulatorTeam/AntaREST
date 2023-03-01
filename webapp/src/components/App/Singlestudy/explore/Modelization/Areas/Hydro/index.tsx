import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import TabWrapper from "../../../TabWrapper";
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
      <TabWrapper study={study} tabStyle="normal" tabList={tabList} />
    </Root>
  );
}

export default Hydro;
