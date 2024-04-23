import { Paper } from "@mui/material";
import * as R from "ramda";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import { useTranslation } from "react-i18next";
import { StudyMetadata } from "../../../../../common/types";
import PropertiesView from "../../../../common/PropertiesView";
import SplitLayoutView from "../../../../common/SplitLayoutView";
import ListElement from "../common/ListElement";
import AdequacyPatch from "./AdequacyPatch";
import AdvancedParameters from "./AdvancedParameters";
import General from "./General";
import Optimization from "./Optimization";
import TimeSeriesManagement from "./TimeSeriesManagement";
import TableMode from "../../../../common/TableMode";

function Configuration() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [currentTabIndex, setCurrentTabIndex] = useState(0);
  const { t } = useTranslation();

  // TODO i18n
  const tabList = useMemo(
    () =>
      [
        { id: 0, name: "General" },
        { id: 1, name: "Time-series management" },
        { id: 2, name: "Optimization preferences" },
        Number(study.version) >= 830 && { id: 3, name: "Adequacy Patch" },
        { id: 4, name: "Advanced parameters" },
        { id: 5, name: t("study.configuration.economicOpt") },
        { id: 6, name: t("study.configuration.geographicTrimmingAreas") },
        { id: 7, name: t("study.configuration.geographicTrimmingLinks") },
      ].filter(Boolean),
    [study.version, t],
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
            [R.equals(2), () => <Optimization />],
            [R.equals(3), () => <AdequacyPatch />],
            [R.equals(4), () => <AdvancedParameters />],
            [
              R.equals(5),
              () => (
                <TableMode
                  studyId={study.id}
                  type="areas"
                  columns={[
                    "averageUnsuppliedEnergyCost",
                    "spreadUnsuppliedEnergyCost",
                    "averageSpilledEnergyCost",
                    "spreadSpilledEnergyCost",
                    "nonDispatchablePower",
                    "dispatchableHydroPower",
                    "otherDispatchablePower",
                  ]}
                />
              ),
            ],
            [
              R.equals(6),
              () => (
                <TableMode
                  studyId={study.id}
                  type="areas"
                  columns={["filterYearByYear", "filterSynthesis"]}
                />
              ),
            ],
            [
              R.equals(7),
              () => (
                <TableMode
                  studyId={study.id}
                  type="links"
                  columns={["filterYearByYear", "filterSynthesis"]}
                />
              ),
            ],
          ])(tabList[currentTabIndex].id)}
        </Paper>
      }
    />
  );
}

export default Configuration;
