/* eslint-disable react/no-unstable-nested-components */
import { Paper } from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
import UnderConstruction from "../../../../common/page/UnderConstruction";
import PropertiesView from "../../../../common/PropertiesView";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import ListElement from "../common/ListElement";
import AdvancedParameters from "./AdvancedParameters";
import General from "./General";
import OptimizationPreferences from "./OptimizationPreferences";
import RegionalDistricts from "./RegionalDistricts";

function Configuration() {
  const [currentElementIndex, setCurrentElementIndex] = useState(0);
  // TODO i18n
  const listElement = useMemo(
    () => [
      { name: "General" },
      { name: "Time-series management" },
      { name: "Regional districts" },
      { name: "Optimization preferences" },
      { name: "Advanced parameters" },
    ],
    []
  );

  return (
    <SplitLayoutView
      left={
        <PropertiesView
          mainContent={
            <ListElement
              list={listElement}
              currentElement={listElement[currentElementIndex].name}
              setSelectedItem={(_, index) => {
                setCurrentElementIndex(index);
              }}
            />
          }
        />
      }
      right={
        <Paper sx={{ width: 1, height: 1, padding: 2, overflow: "auto" }}>
          {R.cond([
            [R.equals(0), () => <General />],
            // [R.equals(1), () => <TimeSeriesManagement />],
            [R.equals(1), () => <UnderConstruction />],
            [R.equals(2), () => <RegionalDistricts />],
            [R.equals(3), () => <OptimizationPreferences />],
            [R.equals(4), () => <AdvancedParameters />],
          ])(currentElementIndex)}
        </Paper>
      }
    />
  );
}

export default Configuration;
