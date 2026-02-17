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

interface UseDeleteStudiesOptions {
  onSuccess?: () => void;
}

export function useDeleteStudies(options?: UseDeleteStudiesOptions) {
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { t } = useTranslation();

  return useMutation({
    ...studyMutations.deleteMany(),
    onError: (error) => {
      enqueueErrorSnackbar(t("studies.error.deleteStudies"), toError(error));
    },
    onSuccess: () => {
      options?.onSuccess?.();
    },
  });
}
