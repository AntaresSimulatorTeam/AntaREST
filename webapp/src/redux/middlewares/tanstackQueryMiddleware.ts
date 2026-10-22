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
import { studyQueries } from "@/queries/studies/queries";
import { variantKeys } from "@/queries/variants/keys";
import { createListenerMiddleware, isAnyOf } from "@reduxjs/toolkit";
import type { AppState } from "../ducks";
import { createStudy, deleteStudy, setStudy, updateStudy } from "../ducks/studies";
import { getDeepVariantsIds, getStudiesStatus } from "../selectors";
import { FetchStatus } from "../utils";

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
      queryClient.invalidateQueries({ queryKey: variantKeys.allTree() });
    }
  },
});

tanstackQueryMiddleware.startListening({
  matcher: isAnyOf(createStudy.fulfilled, setStudy.fulfilled),
  effect: () => {
    // Invalidate variant tree queries to include the new study in the trees
    queryClient.invalidateQueries({ queryKey: variantKeys.allTree() });
  },
});

tanstackQueryMiddleware.startListening({
  actionCreator: deleteStudy.fulfilled,
  effect: async ({ payload: studyId }, listenerApi) => {
    // Capture cascaded deletions now, their individual WebSocket events may be missed.
    const originalState = listenerApi.getOriginalState();
    const deletedStudyIds = new Set([studyId, ...getDeepVariantsIds(originalState, studyId)]);
    const hasStudiesSnapshot = getStudiesStatus(originalState) === FetchStatus.Succeeded;
    const favoritesQuery = studyQueries.favorites();
    const { queryKey } = favoritesQuery;

    // Join any refresh before removing the ID, so its response cannot restore it.
    // Reapplying the deletion for a delayed WebSocket echo is then harmless.
    if (queryClient.getQueryState(queryKey)?.fetchStatus === "fetching") {
      // Query observers surface fetch errors, still update any cached data on failure.
      await queryClient.fetchQuery({ ...favoritesQuery, staleTime: 0 }).catch(() => undefined);
    }

    const previousState = queryClient.getQueryState(queryKey);

    queryClient.setQueryData(
      queryKey,
      (old) => old?.filter((favorite) => !deletedStudyIds.has(favorite.studyId)),
      { updatedAt: previousState?.dataUpdatedAt },
    );

    // Recover unknown descendants or missing data, and preserve unrelated invalidations.
    if (!hasStudiesSnapshot || !previousState?.data || previousState.isInvalidated) {
      await queryClient.invalidateQueries({ queryKey }, { cancelRefetch: false });
    }
  },
});

tanstackQueryMiddleware.startListening({
  actionCreator: deleteStudy.fulfilled,
  effect: async (_, listenerApi) => {
    // Variant trees still need a server refresh, coalesce bulk deletion notifications.
    listenerApi.cancelActiveListeners();
    await listenerApi.delay(100);

    await queryClient.invalidateQueries({ queryKey: variantKeys.allTree() });
  },
});

export default tanstackQueryMiddleware;
