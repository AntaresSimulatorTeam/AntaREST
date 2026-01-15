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

import { bindingConstraintQueries } from "@/queries/bindingConstraints";
import type { QueryList } from "@/queries/types";
import type { BindingConstraint } from "@/services/api/studies/bindingConstraints/type";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";

function useBindingConstraint() {
  const { studyId, bindingConstraintId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/binding-constraints/$bindingConstraintId",
  });
  const { t } = useTranslation();

  const getConstraint = useCallback(
    (constraints: QueryList<BindingConstraint>) => {
      return constraints.find(({ id }) => id === bindingConstraintId);
    },
    [bindingConstraintId],
  );

  const { data: constraint } = useSuspenseQuery({
    ...bindingConstraintQueries.list(studyId),
    select: getConstraint,
  });

  if (!bindingConstraintId) {
    throw new Error(t("route.noParameter", { param: "bindingConstraintId" }));
  }

  if (!constraint) {
    throw new Error(t("study.modeling.bindingConst.notFound", { id: bindingConstraintId }));
  }

  return constraint;
}

export default useBindingConstraint;
