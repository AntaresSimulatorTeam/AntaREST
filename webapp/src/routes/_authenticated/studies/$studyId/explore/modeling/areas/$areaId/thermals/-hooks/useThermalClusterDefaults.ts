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

import { thermalQueries } from "@/queries/thermals/queries";
import type { GetThermalClusterParams } from "@/services/api/studies/areas/thermals/types";
import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { adaptThermalClusterToView } from "../-adapters";

/**
 * Load form defaults once from the shared list, without resetting edits on refetch.
 *
 * @param params - Cluster scope.
 * @param params.studyId - Study identifier.
 * @param params.areaId - Area identifier.
 * @param params.clusterId - Cluster identifier from the route.
 * @returns An async defaults loader for Form, sharing the complete list cache.
 */
function useThermalClusterDefaults({ studyId, areaId, clusterId }: GetThermalClusterParams) {
  const queryClient = useQueryClient();
  const { t } = useTranslation();

  return useCallback(async () => {
    const clusters = await queryClient.fetchQuery(thermalQueries.list(studyId, areaId));
    const cluster = clusters.find(({ id }) => id === clusterId);

    if (!cluster) {
      throw new Error(t("study.modeling.thermals.notFound", { id: clusterId }));
    }

    return adaptThermalClusterToView(cluster);
  }, [queryClient, studyId, areaId, clusterId, t]);
}

export default useThermalClusterDefaults;
