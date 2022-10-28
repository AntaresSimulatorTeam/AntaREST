import { useOutletContext } from "react-router";
import { useMemo } from "react";
import { StudyMetadata } from "../../../../../../../../common/types";
import TabWrapper from "../../../../TabWrapper";

function TimeSeries() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();

  const tabList = useMemo(
    () => [
      {
        label: "Hydro Storage",
        path: `/studies/${study.id}/explore/modelization/area/hydro/timeseries/hydrostorage`,
      },
      {
        label: "Run Of The River",
        path: `/studies/${study.id}/explore/modelization/area/hydro/timeseries/ror`,
      },
    ],
    [study.id]
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabWrapper study={study} tabStyle="normal" tabList={tabList} />;
}

export default TimeSeries;
