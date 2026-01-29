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

import { bindingConstraintMutations } from "@/queries/bindingConstraints/mutations";
import { bindingConstraintQueries } from "@/queries/bindingConstraints/queries";
import { useMutation } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";

function useUpdateBindingConstraint() {
  const { studyId } = useParams({
    from: "/_authenticated/studies/$studyId/explore/modeling/binding-constraints",
  });

  const { queryKey: queryListKey } = bindingConstraintQueries.list(studyId);

  const mutation = useMutation({
    ...bindingConstraintMutations.update(studyId),
    onSuccess: (updatedConstraint, variables, onMutateResult, context) => {
      context.client.setQueryData(queryListKey, (old = []) => {
        return old.map((constraint) =>
          constraint.id === updatedConstraint.id ? updatedConstraint : constraint,
        );
      });
    },
  });

  return mutation;
}

export default useUpdateBindingConstraint;
