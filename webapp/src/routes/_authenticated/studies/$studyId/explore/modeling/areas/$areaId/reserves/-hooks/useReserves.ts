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

import { reserveQueries } from "@/queries/reserves/queries";
import type { Reserve, ReservesParams } from "@/services/api/studies/areas/reserves/types";
import { useSuspenseQuery } from "@tanstack/react-query";

interface Params<TData = Reserve[]> extends ReservesParams {
  select?: (data: Reserve[]) => TData;
}

function useReserves<TData = Reserve[]>({ studyId, areaId, select }: Params<TData>) {
  return useSuspenseQuery({ ...reserveQueries.list(studyId, areaId), select });
}

export default useReserves;
