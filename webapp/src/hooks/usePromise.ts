/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useCallback, useEffect, useState } from "react";
import { usePromise as usePromiseWrapper } from "react-use";
import { isDependencyList } from "../utils/reactUtils";

export const PromiseStatus = {
  Idle: "idle",
  Pending: "pending",
  Fulfilled: "fulfilled",
  Rejected: "rejected",
} as const;

export type TPromiseStatus = (typeof PromiseStatus)[keyof typeof PromiseStatus];

export interface UsePromiseResponse<T> {
  data: T | undefined;
  status: TPromiseStatus;
  isLoading: boolean;
  isFulfilled: boolean;
  isRejected: boolean;
  error: Error | string | undefined;
  reload: () => void;
}

export interface UsePromiseParams {
  resetDataOnReload?: boolean;
  resetErrorOnReload?: boolean;
  deps?: React.DependencyList;
}

type DepsOrParams = React.DependencyList | UsePromiseParams;

function toParams(value: DepsOrParams = {}): UsePromiseParams {
  return isDependencyList(value) ? { deps: value } : value;
}

function usePromise<T>(
  fn: () => Promise<T>,
  params?: DepsOrParams,
): UsePromiseResponse<T> {
  const { deps = [], resetDataOnReload, resetErrorOnReload } = toParams(params);
  const [data, setData] = useState<T>();
  const [status, setStatus] = useState<TPromiseStatus>(PromiseStatus.Idle);
  const [error, setError] = useState<Error | string | undefined>();
  const [reloadCount, setReloadCount] = useState(0);
  const reload = useCallback(() => setReloadCount((prev) => prev + 1), []);
  const mounted = usePromiseWrapper();

  useEffect(
    () => {
      setStatus(PromiseStatus.Pending);
      // Reset
      if (resetDataOnReload) {
        setData(undefined);
      }
      if (resetErrorOnReload) {
        setError(undefined);
      }

      mounted(fn())
        .then((res) => {
          setData(res);
          setStatus(PromiseStatus.Fulfilled);
        })
        .catch((err) => {
          setError(err);
          setStatus(PromiseStatus.Rejected);
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [reloadCount, ...deps],
  );

  return {
    data,
    status,
    isLoading:
      status === PromiseStatus.Idle || status === PromiseStatus.Pending,
    isFulfilled: status === PromiseStatus.Fulfilled,
    isRejected: status === PromiseStatus.Rejected,
    error,
    reload,
  };
}

export default usePromise;
