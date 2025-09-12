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

import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../../types/types";
import TabWrapper from "../../../TabWrapper";
import { getAdvancedParamsFormFields } from "../../../Configuration/AdvancedParameters/utils";

function Hydro() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const studyVersion = Number(study.version);
  const [hydroPmax, setHydroPmax] = useState<string>("");

  useEffect(() => {
    getAdvancedParamsFormFields(study.id).then((data) => {
      setHydroPmax(data.hydroPmax || "");
    });
  }, [study.id]);

  const tabList = useMemo(() => {
    const basePath = `/studies/${study?.id}/explore/modelization/area/${encodeURI(areaId)}/hydro`;
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
      studyVersion >= 860 && { label: "Min Gen", path: `${basePath}/mingen` },
      ...(studyVersion >= 920 && hydroPmax === "hourly"
        ? [
            { label: "Max Pump Power", path: `${basePath}/maxHourlyPumpPower` },
            { label: "Max Gen Power", path: `${basePath}/maxHourlyGenPower` },
            { label: "Max Pump Energy", path: `${basePath}/maxDailyPumpEnergy` },
            { label: "Max Gen Energy", path: `${basePath}/maxDailyGenEnergy` },
          ]
        : []),
    ].filter(Boolean);
  }, [areaId, study?.id, studyVersion, hydroPmax]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return <TabWrapper study={study} tabList={tabList} />;
}

export default Hydro;
