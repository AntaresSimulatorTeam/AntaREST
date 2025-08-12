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

import { toError } from "@/utils/fnUtils";
import { useCallback, useEffect, useRef, useState } from "react";
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
  reload: () => Promise<T>;
}

export interface UsePromiseParams<T> {
  resetDataOnReload?: boolean;
  resetErrorOnReload?: boolean;
  onDataChange?: (data: T | undefined) => void;
  deps?: React.DependencyList;
}

type DepsOrParams<T> = React.DependencyList | UsePromiseParams<T>;

function toParams<T>(value: DepsOrParams<T> = {}): UsePromiseParams<T> {
  return isDependencyList(value) ? { deps: value } : value;
}

function usePromise<T>(fn: () => Promise<T>, params?: DepsOrParams<T>): UsePromiseResponse<T> {
  const { deps = [], resetDataOnReload, resetErrorOnReload, onDataChange } = toParams(params);
  const [data, setData] = useState<T>();
  const [status, setStatus] = useState<TPromiseStatus>(PromiseStatus.Idle);
  const [error, setError] = useState<Error | undefined>();
  const [reloadCount, setReloadCount] = useState(0);

  const reloadPromise = useRef<{
    resolve: (data: T) => void;
    reject: (err: typeof error) => void;
  } | null>(null);

  const reload = useCallback(() => {
    setReloadCount((prev) => prev + 1);

    return new Promise<T>((resolve, reject) => {
      reloadPromise.current = { resolve, reject };
    });
  }, []);

  useEffect(() => {
    let active = true; // Prevent race condition

    setStatus(PromiseStatus.Pending);

    // Reset
    if (resetDataOnReload) {
      setData(undefined);
      onDataChange?.(undefined);
    }
    if (resetErrorOnReload) {
      setError(undefined);
    }

    fn()
      .then((res) => {
        if (active) {
          setData(res);
          onDataChange?.(res);
          setStatus(PromiseStatus.Fulfilled);
          reloadPromise.current?.resolve(res);
        }
      })
      .catch((err) => {
        if (active) {
          const errObj = toError(err);
          setError(errObj);
          setStatus(PromiseStatus.Rejected);
          reloadPromise.current?.reject(errObj);
        }
      })
      .finally(() => {
        if (active) {
          reloadPromise.current = null;
        }
      });

    return () => {
      active = false;
    };
  }, [reloadCount, ...deps]);

  return {
    data,
    status,
    isLoading: status === PromiseStatus.Idle || status === PromiseStatus.Pending,
    isFulfilled: status === PromiseStatus.Fulfilled,
    isRejected: status === PromiseStatus.Rejected,
    error,
    reload,
  };
}

export default usePromise;
