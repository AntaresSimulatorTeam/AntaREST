import * as R from "ramda";
import { PromiseStatus, UsePromiseResponse } from "../../../hooks/usePromise";
import SimpleLoader from "../loaders/SimpleLoader";
import SimpleContent from "../page/SimpleContent";

export interface UsePromiseCondProps<
  T,
  Response extends UsePromiseResponse<T> = UsePromiseResponse<T>
> {
  response: Response;
  ifPending?: () => React.ReactNode;
  ifRejected?: (error: Response["error"]) => React.ReactNode;
  ifResolved?: (data: T) => React.ReactNode;
}

function UsePromiseCond<T>(props: UsePromiseCondProps<T>) {
  const {
    response,
    ifPending = () => <SimpleLoader />,
    ifRejected = (error) => <SimpleContent title={error?.toString()} />,
    ifResolved,
  } = props;
  const { status, data, error } = response;

  return (
    <>
      {R.cond([
        [
          R.either(
            R.equals(PromiseStatus.Idle),
            R.equals(PromiseStatus.Pending)
          ),
          () => ifPending(),
        ],
        [R.equals(PromiseStatus.Rejected), () => ifRejected(error)],
        [R.equals(PromiseStatus.Resolved), () => ifResolved?.(data as T)],
      ])(status)}
    </>
  );
}

export default UsePromiseCond;
