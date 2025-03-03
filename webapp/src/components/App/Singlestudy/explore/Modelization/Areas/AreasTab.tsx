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

import { useEffect, useMemo } from "react";
import { useLocation, useNavigate, useOutletContext } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { StudyMetadata } from "../../../../../../types/types";
import TabWrapper from "../../TabWrapper";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentAreaId } from "../../../../../../redux/selectors";

interface Props {
  renewablesClustering: boolean;
}

function AreasTab({ renewablesClustering }: Props) {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const areaId = useAppSelector(getCurrentAreaId);
  const [t] = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Updates the URL path to include the current areaId.
   *
   * The effect splits the current path, replaces the segment immediately after 'area'
   * with the new areaId, and navigates to this updated path. It ensures the rest of the
   * path, especially in deeply nested URLs, remains unchanged.
   */
  useEffect(() => {
    const currentPath = location.pathname;
    const pathSegments = currentPath.split("/");

    const areaIndex = pathSegments.findIndex((segment) => segment === "area");
    if (areaIndex >= 0 && areaIndex + 1 < pathSegments.length) {
      // replace only the segment after 'area' with the new areaId
      pathSegments[areaIndex + 1] = areaId.toString();

      const newPath = pathSegments.join("/");
      if (newPath !== currentPath) {
        navigate(newPath, { replace: true });
      }
    }
  }, [areaId, navigate, location.pathname]);

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
