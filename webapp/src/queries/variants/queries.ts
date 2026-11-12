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
import { getVariantTree } from "@/services/api/studies/variants";
import type { VariantTree } from "@/services/api/studies/variants/types";
import { createListFromTree } from "@/services/utils";
import { notifyManager, queryOptions } from "@tanstack/react-query";
import { variantKeys } from "./keys";

export const variantQueries = {
  treeDetail: (studyId: Study["id"]) => {
    return queryOptions({
      queryKey: variantKeys.treeDetail(studyId),
      queryFn: async ({ client, signal }) => {
        const tree = await getVariantTree({ studyId, fromRoot: true, signal });

        // Update the cache for all studies in the tree except the current one.
        // `getVariantTree` returns the same tree structure for all studies in the tree.
        notifyManager.batch(() => {
          for (const item of createListFromTree(tree)) {
            // Skip the current study as it is the key being fetched
            if (item.id === studyId) {
              continue;
            }
            client.setQueryData<VariantTree>(variantKeys.treeDetail(item.id), tree);
          }
        });

        return tree;
      },
    });
  },
};
