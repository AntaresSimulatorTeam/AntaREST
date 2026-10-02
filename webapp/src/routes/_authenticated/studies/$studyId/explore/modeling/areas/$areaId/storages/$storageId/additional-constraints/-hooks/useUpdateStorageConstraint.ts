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

import { storageMutations } from "@/queries/storages/mutations";
import { storageQueries } from "@/queries/storages/queries";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

function useUpdateStorageConstraint() {
  const { studyId, areaId, storageId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId",
  });
  const queryClient = useQueryClient();

  const mutation = useMutation({
    ...storageMutations.updateConstraint(studyId, areaId, storageId),
    onSuccess: (updatedConstraint) => {
      const { queryKey: queryListKey } = storageQueries.constraintList(studyId, areaId, storageId);

      queryClient.setQueryData(queryListKey, (old = []) => {
        return old.map((constraint) =>
          constraint.id === updatedConstraint.id ? updatedConstraint : constraint,
        );
      });
    },
  });

  return mutation;
}

export default useUpdateStorageConstraint;
