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

import type {
  ThermalCluster,
  ThermalClusterParams,
} from "@/services/api/studies/areas/thermals/types";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useThermalClusters from "../../-hooks/useThermalClusters";

function useThermalCluster({ studyId, areaId, thermalId }: ThermalClusterParams) {
  const { t } = useTranslation();

  const getThermal = useCallback(
    (thermals: ThermalCluster[]) => {
      return thermals.find(({ id }) => id === thermalId);
    },
    [thermalId],
  );

  const { data: thermal, ...restResult } = useThermalClusters({
    studyId,
    areaId,
    select: getThermal,
  });

  if (!thermalId) {
    throw new Error(t("route.noParameter", { param: "thermalId" }));
  }

  if (!thermal) {
    throw new Error(t("study.modeling.clusters.notFound", { id: thermalId }));
  }

  return { data: thermal, ...restResult };
}

export default useThermalCluster;
