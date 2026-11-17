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

import { variantQueries } from "@/queries/variants/queries";
import type { Study } from "@/services/api/studies/types";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { useSuspenseQuery } from "@tanstack/react-query";

interface Params<TData = VariantTree> {
  studyId: Study["id"];
  select?: (tree: VariantTree) => TData;
}

function useStudyVariantTree<TData = VariantTree>({ studyId, select }: Params<TData>) {
  return useSuspenseQuery({ ...variantQueries.treeDetail(studyId), select });
}

export default useStudyVariantTree;
