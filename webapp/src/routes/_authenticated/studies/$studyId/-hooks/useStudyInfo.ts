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

import type { Study } from "@/services/api/studies/types";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { getDescendantCount, getParentNode } from "@/services/utils";
import { useCallback } from "react";
import useStudyVariantTree from "./useStudyVariantTree";

interface Params {
  studyId: Study["id"];
}

function useStudyInfo({ studyId }: Params) {
  const select = useCallback(
    (variantTree: VariantTree) => {
      const referenceStudy = variantTree.node;
      const isReference = studyId === referenceStudy.id;

      return {
        variantTree,
        referenceStudy,
        parentStudy: getParentNode(variantTree, studyId),
        descendantCount: getDescendantCount(variantTree, studyId),
        isReference,
        isVariant: !isReference,
        // When the reference study is archived, all its variants are considered archived as well
        isArchived: referenceStudy.archived,
      };
    },
    [studyId],
  );

  return useStudyVariantTree({ studyId, select });
}

export default useStudyInfo;
