import { useCallback, useEffect, useState } from "react";
import { usePromise as usePromiseWrapper } from "react-use";
import { isDependencyList } from "../utils/reactUtils";

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
  resetErrorOnReload?: boolean;
  deps?: React.DependencyList;
}

type DepsOrParams = React.DependencyList | UsePromiseParams;

function toParams(value: DepsOrParams = {}): UsePromiseParams {
  return isDependencyList(value) ? { deps: value } : value;
}

function usePromise<T>(
  fn: () => Promise<T>,
  params?: DepsOrParams
): UsePromiseResponse<T> {
  const { deps = [], resetDataOnReload, resetErrorOnReload } = toParams(params);
  const [data, setData] = useState<T>();
  const [status, setStatus] = useState(PromiseStatus.Idle);
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
