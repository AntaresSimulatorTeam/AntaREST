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

import { type SnackbarKey, useSnackbar } from "notistack";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import { toError } from "../utils/fnUtils";
import { useCallback } from "react";
import useUpdatedRef from "./useUpdatedRef";

interface UsePromiseHandlerParams<T extends unknown[], U> {
  fn: (...args: T) => Promise<U>;
  errorMessage: string;
  successMessage?: string;
  pendingMessage?: string;
}

/**
 * Handles a promise with a `try...catch` and displays a snackbar to report status.
 *
 * @param params - The parameters.
 * @returns The promise handler.
 */
function usePromiseHandler<T extends unknown[], U>(params: UsePromiseHandlerParams<T, U>) {
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const paramsRef = useUpdatedRef(params);

  const handlePromise = useCallback(
    async (...args: T) => {
      const { fn, errorMessage, successMessage, pendingMessage } = paramsRef.current;

      let snackbarKey: SnackbarKey = "";
      let timeoutId = -1;

      if (pendingMessage) {
        // Show a pending message only if the operation takes longer than 750ms
        timeoutId = window.setTimeout(() => {
          snackbarKey = enqueueSnackbar(pendingMessage, {
            variant: "info",
            persist: true,
            hideIconVariant: true,
          });
        }, 750);
      }

      const closePendingSnackbar = () => {
        clearTimeout(timeoutId);
        closeSnackbar(snackbarKey);
      };

      try {
        const result = await fn(...args);

        closePendingSnackbar();

        if (successMessage !== undefined) {
          enqueueSnackbar(successMessage, {
            variant: "success",
          });
        }

        return result;
      } catch (err) {
        closePendingSnackbar();

        enqueueErrorSnackbar(errorMessage, toError(err));
      }
    },
    [closeSnackbar, enqueueErrorSnackbar, enqueueSnackbar],
  );

  return handlePromise;
}

export default usePromiseHandler;
