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
  RenewableCluster,
  RenewableClusterParams,
} from "@/services/api/studies/areas/renewables/types";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useRenewableClusters from "../../-hooks/useRenewableClusters";

function useRenewableCluster({ studyId, areaId, renewableId }: RenewableClusterParams) {
  const { t } = useTranslation();

  const getRenewable = useCallback(
    (renewables: RenewableCluster[]) => {
      return renewables.find(({ id }) => id === renewableId);
    },
    [renewableId],
  );

  const { data: renewable } = useRenewableClusters({ studyId, areaId, select: getRenewable });

  if (!renewableId) {
    throw new Error(t("route.noParameter", { param: "renewableId" }));
  }

  if (!renewable) {
    throw new Error(t("study.modeling.clusters.notFound", { id: renewableId }));
  }

  return renewable;
}

export default useRenewableCluster;
