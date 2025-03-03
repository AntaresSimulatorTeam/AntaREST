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

import * as R from "ramda";
import { useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../types/types";
import PropertiesView from "../../../../common/PropertiesView";
import ListElement from "../common/ListElement";
import AdequacyPatch from "./AdequacyPatch";
import AdvancedParameters from "./AdvancedParameters";
import General from "./General";
import Optimization from "./Optimization";
import TimeSeriesManagement from "./TimeSeriesManagement";
import TableMode from "../../../../common/TableMode";
import SplitView from "../../../../common/SplitView";
import ViewWrapper from "../../../../common/page/ViewWrapper";

function Configuration() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [currentTabIndex, setCurrentTabIndex] = useState(0);
  const { t } = useTranslation();

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
        {
          id: 8,
          name: t("study.configuration.geographicTrimmingBindingConstraints"),
        },
      ].filter(Boolean),
    [study.version, t],
  );

  return (
    <SplitView id="configuration" sizes={[15, 85]}>
      {/* Left */}
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
      {/* Right */}
      <ViewWrapper>
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
          [
            R.equals(8),
            () => (
              <TableMode
                studyId={study.id}
                type="binding-constraints"
                columns={["filterYearByYear", "filterSynthesis"]}
              />
            ),
          ],
        ])(tabList[currentTabIndex].id)}
      </ViewWrapper>
    </SplitView>
  );
}

export default Configuration;
