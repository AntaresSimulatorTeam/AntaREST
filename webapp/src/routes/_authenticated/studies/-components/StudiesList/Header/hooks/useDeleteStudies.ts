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

import { useMutation } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { studyMutations } from "@/queries/studies/mutations";
import { toError } from "@/utils/fnUtils";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { deleteStudy } from "@/redux/ducks/studies";

interface UseDeleteStudiesOptions {
  onSuccess?: () => void;
}

export function useDeleteStudies(options?: UseDeleteStudiesOptions) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  return useMutation({
    ...studyMutations.deleteMany(),
    onError: (error) => {
      enqueueErrorSnackbar(t("studies.error.deleteStudies"), toError(error));
    },
    onSuccess: (_data, variables) => {
      // TEMPORARY: Manually update Redux store for immediate UI feedback
      // since WebSocket events may be delayed or lost

      // TODO: Remove once migrated to React Query for state management
      // The proper solution is to invalidate React Query cache here
      variables.studyIds.forEach((studyId) => {
        dispatch(
          deleteStudy({
            name: "", // Pass 'name' to trigger WebSocket code path (avoids redundant API calls)
            id: studyId,
          }),
        );
      });

      options?.onSuccess?.();
    },
  });
}
