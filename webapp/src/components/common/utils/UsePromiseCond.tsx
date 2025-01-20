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

import { PromiseStatus, UsePromiseResponse } from "../../../hooks/usePromise";
import SimpleLoader from "../loaders/SimpleLoader";
import EmptyView from "../page/EmptyView";

export type Response<T = unknown> = Pick<
  UsePromiseResponse<T>,
  "data" | "status" | "error"
>;

export function mergeResponses<T1, T2>(
  res1: Response<T1>,
  res2: Response<T2>,
): Response<[T1, T2]> {
  function getMergedStatus() {
    const preResolvedStatus = [
      PromiseStatus.Idle,
      PromiseStatus.Pending,
      PromiseStatus.Rejected,
    ].find((status) => res1.status === status || res2.status === status);

    return preResolvedStatus || PromiseStatus.Fulfilled;
  }

  const status = getMergedStatus();

  return {
    ...res1,
    ...res2,
    status,
    data:
      status === PromiseStatus.Fulfilled
        ? [res1.data as T1, res2.data as T2]
        : undefined,
    error: res1.error || res2.error,
  };
}

export interface UsePromiseCondProps<T> {
  response: Response<T>;
  ifPending?: () => React.ReactNode;
  ifRejected?: (error: Response["error"]) => React.ReactNode;
  ifFulfilled?: (data: T) => React.ReactNode;
  keepLastResolvedOnReload?: boolean;
}

function UsePromiseCond<T>(props: UsePromiseCondProps<T>) {
  const {
    response,
    ifPending = () => <SimpleLoader />,
    ifRejected = (error) => <EmptyView title={error?.toString()} />,
    ifFulfilled,
    keepLastResolvedOnReload = false,
  } = props;

  const { status, data, error } = response;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const hasToKeepLastResolved = () => {
    return data !== undefined && keepLastResolvedOnReload;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Keep this condition at the top
  if (status === PromiseStatus.Fulfilled || hasToKeepLastResolved()) {
    return ifFulfilled?.(data as T);
  }

  if (status === PromiseStatus.Idle || status === PromiseStatus.Pending) {
    return ifPending();
  }

  if (status === PromiseStatus.Rejected) {
    return ifRejected(error);
  }
}

export default UsePromiseCond;
