/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import ViewWrapper from "@/components/page/ViewWrapper";
import TabsView from "@/components/TabsView";
import { createFileRoute } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import useStudy from "../../-hooks/useStudy";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/configuration")({
  component: ConfigurationLayout,
});

function ConfigurationLayout() {
  const study = useStudy();
  const { t } = useTranslation();

  // const tabList = useMemo(
  //   () =>
  //     [
  //       { id: 0, name: "General" },
  //       { id: 1, name: "Time-series management" },
  //       { id: 2, name: "Optimization preferences" },
  //       Number(study.version) >= 830 && { id: 3, name: "Adequacy Patch" },
  //       { id: 4, name: "Advanced parameters" },
  //       { id: 5, name: t("study.configuration.economicOpt") },
  //       { id: 6, name: t("study.configuration.geographicTrimmingAreas") },
  //       { id: 7, name: t("study.configuration.geographicTrimmingLinks") },
  //       {
  //         id: 8,
  //         name: t("study.configuration.geographicTrimmingBindingConstraints"),
  //       },
  //     ].filter(Boolean),
  //   [study.version, t],
  // );

  return (
    <TabsView
      items={[
        {
          label: "General",
          linkOptions: {
            to: "/studies/$studyId/explore/configuration/general",
            params: { studyId: study.id },
          },
        },
        {
          label: "Time-Series Generation",
          linkOptions: {
            to: "/studies/$studyId/explore/configuration/ts-generation",
            params: { studyId: study.id },
          },
        },
        {
          label: "Optimization",
          linkOptions: {
            to: "/studies/$studyId/explore/configuration/optimization",
            params: { studyId: study.id },
          },
        },
      ]}
      renderPanel={({ children }) => <ViewWrapper>{children}</ViewWrapper>}
    />
    // <SplitView splitId="configuration">
    //   {/* Left */}
    //   <PropertiesView
    //     mainContent={
    //       <ListElement
    //         list={tabList}
    //         currentElement={tabList[currentTabIndex].name}
    //         setSelectedItem={(_, index) => {
    //           setCurrentTabIndex(index);
    //         }}
    //       />
    //     }
    //   />
    //   {/* Right */}
    //   <ViewWrapper>
    //     {R.cond([
    //       [R.equals(0), () => <General />],
    //       [R.equals(1), () => <TimeSeriesManagement />],
    //       [R.equals(2), () => <Optimization />],
    //       [R.equals(3), () => <AdequacyPatch />],
    //       [R.equals(4), () => <AdvancedParameters />],
    //       [
    //         R.equals(5),
    //         () => (
    //           <TableMode
    //             studyId={study.id}
    //             type="areas"
    //             columns={[
    //               "energyCostUnsupplied",
    //               "spreadUnsuppliedEnergyCost",
    //               "energyCostSpilled",
    //               "spreadSpilledEnergyCost",
    //               "nonDispatchPower",
    //               "dispatchHydroPower",
    //               "otherDispatchPower",
    //             ]}
    //           />
    //         ),
    //       ],
    //       [
    //         R.equals(6),
    //         () => (
    //           <TableMode
    //             studyId={study.id}
    //             type="areas"
    //             columns={["filterByYear", "filterSynthesis"]}
    //           />
    //         ),
    //       ],
    //       [
    //         R.equals(7),
    //         () => (
    //           <TableMode
    //             studyId={study.id}
    //             type="links"
    //             columns={["filterYearByYear", "filterSynthesis"]}
    //           />
    //         ),
    //       ],
    //       [
    //         R.equals(8),
    //         () => (
    //           <TableMode
    //             studyId={study.id}
    //             type="binding-constraints"
    //             columns={["filterYearByYear", "filterSynthesis"]}
    //           />
    //         ),
    //       ],
    //     ])(tabList[currentTabIndex].id)}
    //   </ViewWrapper>
    // </SplitView>
  );
}
