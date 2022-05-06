import { DependencyList, useEffect } from "react";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import usePromise, { UsePromiseResponse, UsePromiseParams } from "./usePromise";

export interface UsePromiseWithSnackbarErrorParams extends UsePromiseParams {
  errorMessage: string;
}

function usePromiseWithSnackbarError<T>(
  fn: () => Promise<T>,
  params: UsePromiseWithSnackbarErrorParams,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const res = usePromise(fn, params, deps);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { errorMessage } = params;

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
