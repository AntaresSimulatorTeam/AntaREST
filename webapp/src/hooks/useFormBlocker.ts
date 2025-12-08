/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import useDialogManager from "@/hooks/useDialogManager";
import { useBlocker } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export interface UseFormBlockerParams {
  isSubmitting: boolean;
  isDirty: boolean;
  disabled?: boolean;
}

/**
 * Hook that protects a form from being closed (view transitions, tab/browser closed) by showing
 * a confirmation dialog if the form is dirty or submitting.
 *
 * Only work with navigation managed by Tanstack Router.
 *
 * Commonly used in components containing forms.
 *
 * @param params - The parameters.
 * @param params.isSubmitting - Whether the form is being submitted.
 * @param params.isDirty - Whether the form is dirty (has unsaved changes).
 * @param params.disabled - If true, the hook is disabled and does not block navigation.
 */
function useFormBlocker({ isSubmitting, isDirty, disabled }: UseFormBlockerParams) {
  const { confirm } = useDialogManager();
  const { t } = useTranslation();

  useBlocker({
    shouldBlockFn: async () => {
      if (!isSubmitting && !isDirty) {
        return false;
      }

      const shouldAllow = await confirm({
        content: isSubmitting ? t("form.submit.inProgress") : t("form.changeNotSaved"),
        alert: "warning",
      });

      return !shouldAllow;
    },
    withResolver: true,
    disabled,
  });
}

export default useFormBlocker;
