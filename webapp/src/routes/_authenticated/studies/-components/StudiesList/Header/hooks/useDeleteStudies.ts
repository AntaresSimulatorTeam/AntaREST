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

export function useDeleteStudies() {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const dispatch = useAppDispatch();
  const { t } = useTranslation();

  return useMutation({
    ...studyMutations.deleteMany(),
    onError: (error) => {
      enqueueErrorSnackbar(t("studies.error.deleteStudies"), toError(error));
    },
    onSuccess: async (_data, { studyIds }) => {
      // WebSocket events may be delayed or lost. Update Redux before closing the dialog.
      // TODO: Remove this bridge when the study list moves to TanStack Query.
      await Promise.all(
        studyIds.map((studyId) =>
          dispatch(
            deleteStudy({
              name: "", // Use the local confirmation path without another DELETE request.
              id: studyId,
            }),
          ).unwrap(),
        ),
      );
    },
  });
}
