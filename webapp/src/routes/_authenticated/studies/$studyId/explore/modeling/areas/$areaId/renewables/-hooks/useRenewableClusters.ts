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

import { renewableQueries } from "@/queries/renewables/queries";
import type {
  RenewableCluster,
  RenewableClustersParams,
} from "@/services/api/studies/areas/renewables/types";
import { useSuspenseQuery } from "@tanstack/react-query";

interface Params<TData = RenewableCluster[]> extends RenewableClustersParams {
  select?: (data: RenewableCluster[]) => TData;
}

function useRenewableClusters<TData = RenewableCluster[]>({
  studyId,
  areaId,
  select,
}: Params<TData>) {
  return useSuspenseQuery({ ...renewableQueries.list(studyId, areaId), select });
}

export default useRenewableClusters;
