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

import { useSnackbar, type ProviderContext } from "notistack";
import { useCallback } from "react";
import type { L } from "ts-toolbelt";
import SnackErrorMessage from "../components/common/SnackErrorMessage";

type EnqueueErrorType = ProviderContext["enqueueSnackbar"];

type EnqueueErrorSnackbarType = (
  message: L.Head<Parameters<EnqueueErrorType>>,
  details: string | Error,
) => ReturnType<EnqueueErrorType>;

function useEnqueueErrorSnackbar(): EnqueueErrorSnackbarType {
  const { enqueueSnackbar } = useSnackbar();

  return useCallback<EnqueueErrorSnackbarType>(
    (message, details) => {
      return enqueueSnackbar(message, {
        variant: "error",
        persist: true,
        content: (key, msg) => <SnackErrorMessage id={key} message={msg} details={details} />,
      });
    },
    [enqueueSnackbar],
  );
}

export default useEnqueueErrorSnackbar;
