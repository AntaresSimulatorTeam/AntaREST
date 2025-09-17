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

import { setFormStatus } from "@/redux/ducks/ui";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { useUnmount, useUpdateEffect } from "react-use";
import useBlocker from "./useBlocker";
import useFormCloseConfirm from "./useFormCloseConfirm";

export interface UseFormCloseProtectionParams {
  isSubmitting: boolean;
  isDirty: boolean;
}

/**
 * Hook that protects a form from being closed (view transitions, tab/browser closed) by showing
 * a confirmation dialog if the form is dirty or submitting.
 *
 * Commonly used in components containing forms.
 *
 * Note: Only work with view transitions triggered by react-router, to support view transitions
 * without react-router use `useFormCloseConfirm` directly.
 *
 * @see {@link useFormCloseConfirm} Use to show the confirmation dialog.
 *
 * @param params - The parameters.
 * @param params.isSubmitting - Whether the form is being submitted.
 * @param params.isDirty - Whether the form is dirty (has unsaved changes).
 */
function useFormCloseProtection({ isSubmitting, isDirty }: UseFormCloseProtectionParams) {
  const dispatch = useAppDispatch();
  const { withFormCloseCheck } = useFormCloseConfirm();

  useUpdateEffect(() => {
    dispatch(setFormStatus({ isSubmitting, isDirty }));
  }, [dispatch, isDirty, isSubmitting]);

  useUnmount(() => {
    if (isSubmitting || isDirty) {
      dispatch(setFormStatus({ isSubmitting: false, isDirty: false }));
    }
  });

  useBlocker(
    withFormCloseCheck((tx) => {
      tx.retry();
    }),
    isSubmitting || isDirty,
  );
}

export default useFormCloseProtection;
