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

import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";
import type { StudyMetadata } from "../../../../../../types/types";
import TabWrapper from "../../TabWrapper";

interface Props {
  renewablesClustering: boolean;
}

function AreasTab({ renewablesClustering }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();

  const tabList = useMemo(() => {
    const basePath = `/studies/${study.id}/explore/modelization/area/${encodeURI(areaId)}`;

    const tabs = [
      { label: "study.modelization.properties", pathSuffix: "properties" },
      { label: "study.modelization.load", pathSuffix: "load" },
      { label: "study.modelization.thermal", pathSuffix: "thermal" },
      {
        label: "study.modelization.storages",
        pathSuffix: "storages",
        condition: parseInt(study.version, 10) >= 860,
      },
      {
        label: "study.modelization.renewables",
        pathSuffix: "renewables",
        condition: renewablesClustering,
      },
      { label: "study.modelization.hydro", pathSuffix: "hydro" },
      {
        label: "study.modelization.wind",
        pathSuffix: "wind",
        condition: !renewablesClustering,
      },
      {
        label: "study.modelization.solar",
        pathSuffix: "solar",
        condition: !renewablesClustering,
      },
      { label: "study.modelization.reserves", pathSuffix: "reserves" },
      { label: "study.modelization.miscGen", pathSuffix: "miscGen" },
    ];

    return tabs
      .filter(({ condition }) => condition ?? true)
      .map(({ label, pathSuffix }) => ({
        label: t(label),
        path: `${basePath}/${pathSuffix}`,
      }));
  }, [study.id, areaId, renewablesClustering, t, study.version]);

  return <TabWrapper study={study} tabList={tabList} />;
}

export default AreasTab;
