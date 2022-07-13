import * as R from "ramda";
import { PromiseStatus } from "../../../hooks/usePromise";

export interface UsePromiseCondProps {
  status: PromiseStatus;
  ifPending?: React.ReactNode;
  ifRejected?: React.ReactNode;
  ifResolved?: React.ReactNode;
}

function UsePromiseCond(props: UsePromiseCondProps) {
  const { status, ifPending, ifRejected, ifResolved } = props;

  return (
    <>
      {R.cond([
        [
          R.either(
            R.equals(PromiseStatus.Idle),
            R.equals(PromiseStatus.Pending)
          ),
          () => ifPending,
        ],
        [R.equals(PromiseStatus.Rejected), () => ifRejected],
        [R.equals(PromiseStatus.Resolved), () => ifResolved],
      ])(status)}
    </>
  );
}

export default UsePromiseCond;
