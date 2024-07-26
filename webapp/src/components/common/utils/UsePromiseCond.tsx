import * as R from "ramda";
import { PromiseStatus, UsePromiseResponse } from "../../../hooks/usePromise";
import SimpleLoader from "../loaders/SimpleLoader";
import EmptyView from "../page/SimpleContent";

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

    return preResolvedStatus || PromiseStatus.Resolved;
  }

  const status = getMergedStatus();

  return {
    ...res1,
    ...res2,
    status,
    data:
      status === PromiseStatus.Resolved
        ? [res1.data as T1, res2.data as T2]
        : undefined,
    error: res1.error || res2.error,
  };
}

export interface UsePromiseCondProps<T> {
  response: Response<T>;
  ifPending?: () => React.ReactNode;
  ifRejected?: (error: Response["error"]) => React.ReactNode;
  ifResolved?: (data: T) => React.ReactNode;
  keepLastResolvedOnReload?: boolean;
}

function UsePromiseCond<T>(props: UsePromiseCondProps<T>) {
  const {
    response,
    ifPending = () => <SimpleLoader />,
    ifRejected = (error) => <EmptyView title={error?.toString()} />,
    ifResolved,
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

  return (
    <>
      {R.cond([
        // Resolved
        [
          R.either(R.equals(PromiseStatus.Resolved), hasToKeepLastResolved),
          () => ifResolved?.(data as T),
        ],
        // Pending
        [
          R.either(
            R.equals(PromiseStatus.Idle),
            R.equals(PromiseStatus.Pending),
          ),
          () => ifPending(),
        ],
        // Rejected
        [R.equals(PromiseStatus.Rejected), () => ifRejected(error)],
      ])(status)}
    </>
  );
}

export default UsePromiseCond;
