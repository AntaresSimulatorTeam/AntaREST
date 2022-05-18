import { DependencyList, useCallback, useEffect, useState } from "react";
import { usePromise as usePromiseWrapper } from "react-use";

export enum PromiseStatus {
  Idle = "idle",
  Pending = "pending",
  Resolved = "resolved",
  Rejected = "rejected",
}

export interface UsePromiseResponse<T> {
  data: T | undefined;
  status: PromiseStatus;
  isLoading: boolean;
  isResolved: boolean;
  isRejected: boolean;
  error: Error | string | undefined;
  reload: () => void;
}

export interface UsePromiseParams {
  resetDataOnReload?: boolean;
}

function usePromise<T>(
  fn: () => Promise<T>,
  params?: UsePromiseParams,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const [data, setData] = useState<T>();
  const [status, setStatus] = useState(PromiseStatus.Idle);
  const [error, setError] = useState<Error | string | undefined>();
  const [reloadCount, setReloadCount] = useState(0);
  const reload = useCallback(() => setReloadCount((prev) => prev + 1), []);
  const mounted = usePromiseWrapper();
  const resetDataOnReload = params?.resetDataOnReload ?? false;

  useEffect(
    () => {
      setStatus(PromiseStatus.Pending);
      // Reset
      if (resetDataOnReload) {
        setData(undefined);
      }
      setError(undefined);

      mounted(fn())
        .then((res) => {
          setData(res);
          setStatus(PromiseStatus.Resolved);
        })
        .catch((err) => {
          setError(err);
          setStatus(PromiseStatus.Rejected);
        });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [reloadCount, ...deps]
  );

  return {
    data,
    status,
    isLoading:
      status === PromiseStatus.Idle || status === PromiseStatus.Pending,
    isResolved: status === PromiseStatus.Resolved,
    isRejected: status === PromiseStatus.Rejected,
    error,
    reload,
  };
}

export default usePromise;
