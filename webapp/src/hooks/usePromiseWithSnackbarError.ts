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

import { useEffect } from "react";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import usePromise, { type UsePromiseResponse, type UsePromiseParams } from "./usePromise";

export interface UsePromiseWithSnackbarErrorParams extends UsePromiseParams {
  errorMessage: string;
}

function usePromiseWithSnackbarError<T>(
  fn: () => Promise<T>,
  params: UsePromiseWithSnackbarErrorParams,
): UsePromiseResponse<T> {
  const res = usePromise(fn, params);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { errorMessage } = params;

  useEffect(() => {
    if (res.isRejected) {
      enqueueErrorSnackbar(errorMessage, res.error || "");
    }
  }, [enqueueErrorSnackbar, errorMessage, res.error, res.isRejected]);

  return res;
}

export default usePromiseWithSnackbarError;
