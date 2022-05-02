import { DependencyList, useEffect } from "react";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import usePromise, { UsePromiseResponse } from "./usePromise";

function usePromiseWithSnackbarError<T>(
  fn: () => Promise<T>,
  errorMessage: string,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const res = usePromise(fn, deps);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  useEffect(
    () => {
      if (res.error) {
        enqueueErrorSnackbar(errorMessage, res.error);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [res.error]
  );

  return res;
}

export default usePromiseWithSnackbarError;
