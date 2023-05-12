/* eslint-disable react/no-unstable-nested-components */
import { Paper } from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../common/types";
import UnderConstruction from "../../../../common/page/UnderConstruction";
import PropertiesView from "../../../../common/PropertiesView";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import ListElement from "../common/ListElement";
import AdequacyPatch from "./AdequacyPatch";
import AdvancedParameters from "./AdvancedParameters";
import General from "./General";
import Optimization from "./Optimization";
import RegionalDistricts from "./RegionalDistricts";
import TimeSeriesManagement from "./TimeSeriesManagement";

function Configuration() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [currentTabIndex, setCurrentTabIndex] = useState(0);

  // TODO i18n
  const tabList = useMemo(
    () =>
      [
        { id: 0, name: "General" },
        { id: 1, name: "Time-series management" },
        { id: 2, name: "Regional districts" },
        { id: 3, name: "Optimization preferences" },
        Number(study.version) >= 830 && { id: 4, name: "Adequacy Patch" },
        { id: 5, name: "Advanced parameters" },
      ].filter(Boolean),
    [study.version]
  );

  return (
    <SplitLayoutView
      left={
        <PropertiesView
          mainContent={
            <ListElement
              list={tabList}
              currentElement={tabList[currentTabIndex].name}
              setSelectedItem={(_, index) => {
                setCurrentTabIndex(index);
              }}
            />
          }
        />
      }
      right={
        <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
          {R.cond([
            [R.equals(0), () => <General />],
            [R.equals(1), () => <TimeSeriesManagement />],
            [R.equals(1), () => <UnderConstruction />],
            [R.equals(2), () => <RegionalDistricts />],
            [R.equals(3), () => <Optimization />],
            [R.equals(4), () => <AdequacyPatch />],
            [R.equals(5), () => <AdvancedParameters />],
          ])(tabList[currentTabIndex].id)}
        </Paper>
      }
    />
  );
}

export default Configuration;
