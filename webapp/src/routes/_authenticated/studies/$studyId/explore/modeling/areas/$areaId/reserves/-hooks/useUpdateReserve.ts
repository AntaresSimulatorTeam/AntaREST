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

import { reserveMutations } from "@/queries/reserves/mutations";
import { reserveQueries } from "@/queries/reserves/queries";
import type { ReserveParams } from "@/services/api/studies/areas/reserves/types";
import { useMutation, useQueryClient } from "@tanstack/react-query";

function useUpdateReserve({ studyId, areaId, reserveId }: ReserveParams) {
  const queryClient = useQueryClient();

  const { queryKey: queryListKey } = reserveQueries.list(studyId, areaId);

  return useMutation({
    ...reserveMutations.update(studyId, areaId, reserveId),
    onSuccess: async (updatedReserve) => {
      await queryClient.cancelQueries({ queryKey: queryListKey });

      queryClient.setQueryData(queryListKey, (old = []) =>
        old.map((reserve) => (reserve.id === updatedReserve.id ? updatedReserve : reserve)),
      );
    },
  });
}

export default useUpdateReserve;
