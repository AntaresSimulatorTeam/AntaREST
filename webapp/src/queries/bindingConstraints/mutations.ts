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

import {
  createBindingConstraint,
  deleteBindingConstraint,
  duplicateBindingConstraint,
} from "@/services/api/studies/bindingConstraints";
import type { StudyMetadata } from "@/types/types";
import { mutationOptions } from "@tanstack/react-query";
import { bindingConstraintKeys } from "./keys";

export const bindingConstraintMutations = {
  create: (studyId: StudyMetadata["id"]) => {
    return mutationOptions({
      mutationKey: bindingConstraintKeys.create(studyId),
      mutationFn: createBindingConstraint,
    });
  },
  duplicate: (studyId: StudyMetadata["id"]) => {
    return mutationOptions({
      mutationKey: bindingConstraintKeys.duplicate(studyId),
      mutationFn: duplicateBindingConstraint,
    });
  },
  delete: (studyId: StudyMetadata["id"]) => {
    return mutationOptions({
      mutationKey: bindingConstraintKeys.delete(studyId),
      mutationFn: deleteBindingConstraint,
    });
  },
};
