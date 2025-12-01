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

import { setFormStatus } from "@/redux/ducks/ui";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { useEffect } from "react";
import { usePrevious, useUnmount } from "react-use";
import useBlocker from "./useBlocker";
import useFormCloseConfirm from "./useFormCloseConfirm";

export interface UseFormCloseProtectionParams {
  isSubmitting: boolean;
  isDirty: boolean;
  disableHook?: boolean;
}

/**
 * Hook that protects a form from being closed (view transitions, tab/browser closed) by showing
 * a confirmation dialog if the form is dirty or submitting.
 *
 * Commonly used in components containing forms.
 *
 * Note: Only work with view transitions triggered by react-router, to support view transitions
 * without react-router use {@link useFormCloseConfirm} directly.
 *
 * @see {@link useFormCloseConfirm} Use to show the confirmation dialog.
 *
 * @param params - The parameters.
 * @param params.isSubmitting - Whether the form is being submitted.
 * @param params.isDirty - Whether the form is dirty (has unsaved changes).
 * @param params.disableHook - If true, the hook is disabled and does not block navigation.
 *
 * @returns An object with the following property:
 * - `executeWithoutFormCloseCheck`: From {@link useFormCloseConfirm}.
 */
function useFormCloseProtection({
  isSubmitting,
  isDirty,
  disableHook,
}: UseFormCloseProtectionParams) {
  const dispatch = useAppDispatch();
  const { withFormCloseCheck, executeWithoutFormCloseCheck } = useFormCloseConfirm();
  const prevDisableHook = usePrevious(disableHook);

  // Reset form status when the hook is disabled
  if (disableHook && !prevDisableHook) {
    dispatch(setFormStatus({ isSubmitting: false, isDirty: false }));
  }

  // Update form status in the global state
  useEffect(() => {
    if (disableHook) {
      return;
    }

    dispatch(setFormStatus({ isSubmitting, isDirty }));
  }, [disableHook, dispatch, isDirty, isSubmitting]);

  // Reset form status on unmount
  useUnmount(() => {
    if (disableHook) {
      return;
    }

    dispatch(setFormStatus({ isSubmitting: false, isDirty: false }));
  });

  // Block navigation if the form is dirty or submitting and the hook is not disabled
  useBlocker(
    withFormCloseCheck((tx) => {
      tx.retry();
    }),
    !disableHook && (isSubmitting || isDirty),
  );

  return { executeWithoutFormCloseCheck };
}

export default useFormCloseProtection;
