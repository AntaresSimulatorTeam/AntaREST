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

import { storageQueries } from "@/queries/storages/queries";
import type { QueryList } from "@/queries/types";
import type { StorageConstraint } from "@/services/api/studies/areas/storages/types";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

function useStorageConstraint() {
  const { studyId, areaId, storageId, constraintId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/areas/$areaId/storages/$storageId/additional-constraints/$constraintId/",
  });
  const { t } = useTranslation();

  const getConstraint = useCallback(
    (constraints: QueryList<StorageConstraint>) => {
      return constraints.find(({ id }) => id === constraintId);
    },
    [constraintId],
  );

  const { data: constraint } = useSuspenseQuery({
    ...storageQueries.constraintList(studyId, areaId, storageId),
    select: getConstraint,
  });

  if (!constraintId) {
    throw new Error(t("route.noParameter", { param: "constraintId" }));
  }

  if (!constraint) {
    throw new Error(t("study.area.storage.additionalConstraint.notFound", { id: constraintId }));
  }

  return constraint;
}

export default useStorageConstraint;
