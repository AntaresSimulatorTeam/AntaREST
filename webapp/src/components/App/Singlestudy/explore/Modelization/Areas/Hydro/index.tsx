/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { useMemo } from "react";
import { useOutletContext } from "react-router";
import semver from "semver";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../../types/types";
import TabWrapper from "../../../TabWrapper";
import usePromise from "@/hooks/usePromise";
import { getCompatibilityParamsFormFields } from "../../../Configuration/AdvancedParameters/utils";

function Hydro() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);

  const { data: hydroPmax = "" } = usePromise(async () => {
    const values = await getCompatibilityParamsFormFields(study.id);
    return values.hydroPmax;
  }, [study.id]);

  const tabList = useMemo(() => {
    const basePath = `/studies/${study?.id}/explore/modelization/area/${encodeURI(areaId)}/hydro`;

    const hourlyTabs =
      semver.gte(study.version, "9.2.0") && hydroPmax === "hourly"
        ? [
            { label: "Max Hourly Gen Power", path: `${basePath}/maxHourlyGenPower` },
            { label: "Max Hourly Pump Power", path: `${basePath}/maxHourlyPumpPower` },
            { label: "Max Daily Gen Energy", path: `${basePath}/maxDailyGenEnergy` },
            { label: "Max Daily Pump Energy", path: `${basePath}/maxDailyPumpEnergy` },
          ]
        : [];

    return [
      { label: "Management options", path: `${basePath}/management` },
      { label: "Inflow structure", path: `${basePath}/inflow-structure` },
      { label: "Allocation", path: `${basePath}/allocation` },
      { label: "Correlation", path: `${basePath}/correlation` },
      {
        label: "Daily Power & Energy Credits",
        path: `${basePath}/dailypower&energy`,
      },
      { label: "Reservoir levels", path: `${basePath}/reservoirlevels` },
      { label: "Water values", path: `${basePath}/watervalues` },
      { label: "Hydro Storage", path: `${basePath}/hydrostorage` },
      { label: "Run of river", path: `${basePath}/ror` },
      semver.gte(study.version, "8.6.0") && { label: "Min Gen", path: `${basePath}/mingen` },
      ...hourlyTabs,
    ].filter(Boolean);
  }, [areaId, study?.id, study.version, hydroPmax]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabWrapper study={study} tabList={tabList} />;
}

export default Hydro;
