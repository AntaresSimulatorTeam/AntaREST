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

import { setFormCloseDialogStatus } from "@/redux/ducks/ui";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getFormState } from "@/redux/selectors";
import { useCallback, useEffect, useRef } from "react";
import useConfirm from "./useConfirm";
import useUpdatedRef from "./useUpdatedRef";

/**
 * Hook that provides a way to show a confirmation dialog when trying to navigate away from a form
 * that is dirty or submitting.
 *
 * Allow to support view transitions without react-router.
 *
 * @see {@link useFormCloseProtection} Use for view transitions with react-router.
 *
 * @returns An object with the following properties:
 * - `showFormCloseConfirmIfNeeded`: A function that shows the confirmation dialog
 *    if the form is dirty or submitting.
 * - `executeWithFormCloseCheck`: A function that takes a callback and executes it
 *    if the form can be safely closed (not dirty or submitting, or user confirmed).
 * - `executeWithoutFormCloseCheck`: A function that takes a callback and executes it
 *    even if the form is dirty or submitting.
 * - `withFormCloseCheck`: A higher-order function that wraps a function to execute it only
 *    if the form can be safely closed (not dirty or submitting, or user confirmed).
 * - `isPending`: A boolean that indicates if the confirmation dialog is currently shown.
 */
function useFormCloseConfirm() {
  const { showConfirm, isPending, yes, no } = useConfirm();
  const { status, closeDialogStatus } = useAppSelector(getFormState);
  const dispatch = useAppDispatch();
  const forceExecutionRef = useRef(false);
  const dataRef = useUpdatedRef({ status, isPending });

  useEffect(() => {
    if (!isPending) {
      return;
    }

    if (closeDialogStatus === "confirmed") {
      yes();
      dispatch(setFormCloseDialogStatus("closed"));
    } else if (closeDialogStatus === "canceled") {
      no();
      dispatch(setFormCloseDialogStatus("closed"));
    }
  }, [closeDialogStatus, isPending, yes, no, dispatch]);

  const showFormCloseConfirmIfNeeded = useCallback(async () => {
    const { isPending, status } = dataRef.current;

    if (isPending) {
      throw new Error("A promise is already pending");
    }

    if (forceExecutionRef.current) {
      forceExecutionRef.current = false;
      return true;
    }

    if (status.isSubmitting || status.isDirty) {
      dispatch(setFormCloseDialogStatus("opened"));
      const confirm = await showConfirm();
      return !!confirm;
    }

    return true;
  }, [dataRef, dispatch, showConfirm]);

  const executeWithFormCloseCheck = useCallback(
    async <T,>(fn: () => T) => {
      const isConfirmed = await showFormCloseConfirmIfNeeded();
      if (isConfirmed) {
        return fn();
      }
    },
    [showFormCloseConfirmIfNeeded],
  );

  const executeWithoutFormCloseCheck = useCallback(async <T,>(fn: () => T) => {
    forceExecutionRef.current = true;

    // Can be a synchronous or asynchronous function
    const returnValue = await fn();

    // In case `showFormCloseConfirmIfNeeded` has not been called
    forceExecutionRef.current = false;

    return returnValue;
  }, []);

  const withFormCloseCheck = <T extends unknown[], U>(fn: (...args: T) => U) => {
    return (...args: T) => executeWithFormCloseCheck(() => fn(...args));
  };

  return {
    showFormCloseConfirmIfNeeded,
    executeWithFormCloseCheck,
    executeWithoutFormCloseCheck,
    withFormCloseCheck,
    isPending,
  };
}

export default useFormCloseConfirm;
