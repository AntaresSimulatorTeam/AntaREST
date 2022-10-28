import { useMemo } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import TabWrapper from "../../../TabWrapper";

function Hydro() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(
    () => [
      {
        label: "Management options",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/management`,
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
        label: "Time-series",
        path: `/studies/${study?.id}/explore/modelization/area/hydro/timeseries`,
      },
    ],
    [study]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabWrapper study={study} tabStyle="normal" tabList={tabList} />;
}

export default Hydro;
