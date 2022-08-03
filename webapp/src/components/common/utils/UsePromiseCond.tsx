import * as R from "ramda";
import { PromiseStatus, UsePromiseResponse } from "../../../hooks/usePromise";

export interface UsePromiseCondProps<
  T,
  Response extends UsePromiseResponse<T> = UsePromiseResponse<T>
> {
  response: Response;
  ifPending?: () => React.ReactNode;
  ifRejected?: (error: Response["error"]) => React.ReactNode;
  ifResolved?: (data: Response["data"]) => React.ReactNode;
}

function UsePromiseCond<T>(props: UsePromiseCondProps<T>) {
  const { response, ifPending, ifRejected, ifResolved } = props;
  const { status, data, error } = response;

  return (
    <>
      {R.cond([
        [
          R.either(
            R.equals(PromiseStatus.Idle),
            R.equals(PromiseStatus.Pending)
          ),
          () => ifPending?.(),
        ],
        [R.equals(PromiseStatus.Rejected), () => ifRejected?.(error)],
        [R.equals(PromiseStatus.Resolved), () => ifResolved?.(data)],
      ])(status)}
    </>
  );
}

export default UsePromiseCond;
