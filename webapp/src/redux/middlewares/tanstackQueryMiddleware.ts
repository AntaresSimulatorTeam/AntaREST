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

import { queryClient } from "@/queries/queryClient";
import { studyKeys } from "@/queries/studies/keys";
import { studyQueries } from "@/queries/studies/queries";
import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import type { AppState } from "../ducks";
import { createStudy, deleteStudy, setStudy, updateStudy } from "../ducks/studies";

const tanstackQueryMiddleware = createListenerMiddleware<AppState>();

////////////////////////////////////////////////////////////////
// Studies
////////////////////////////////////////////////////////////////

tanstackQueryMiddleware.startListening({
  actionCreator: updateStudy,
  effect: (action) => {
    const studyUpdate = action.payload;
    const newName = studyUpdate.changes.name;

    // If the study name was updated, also update it in the favorites query data to keep it in sync
    if (newName) {
      queryClient.setQueryData(studyQueries.favorites().queryKey, (old) => {
        return old?.map((fav) =>
          fav.studyId === studyUpdate.id ? { ...fav, studyName: newName } : fav,
        );
      });

      // Invalidate variant tree queries to keep the study name up to date in the trees
      queryClient.invalidateQueries({ queryKey: studyKeys.allVariantTree() });
    }
  },
});

tanstackQueryMiddleware.startListening({
  matcher: isAnyOf(createStudy.fulfilled, setStudy.fulfilled),
  effect: () => {
    // Invalidate variant tree queries to include the new study in the trees
    queryClient.invalidateQueries({ queryKey: studyKeys.allVariantTree() });
  },
});

tanstackQueryMiddleware.startListening({
  actionCreator: deleteStudy.fulfilled,
  effect: () => {
    // Invalidate favorites in case the deleted study or its variants were favorites
    queryClient.invalidateQueries({ queryKey: studyKeys.favorites() });

    // Invalidate variant tree queries to remove the deleted study from the trees
    queryClient.invalidateQueries({ queryKey: studyKeys.allVariantTree() });
  },
});

export default tanstackQueryMiddleware;
