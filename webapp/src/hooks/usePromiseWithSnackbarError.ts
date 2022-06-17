import { useEffect } from "react";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import usePromise, { UsePromiseResponse, UsePromiseParams } from "./usePromise";

export interface UsePromiseWithSnackbarErrorParams extends UsePromiseParams {
  errorMessage: string;
}

function usePromiseWithSnackbarError<T>(
  fn: () => Promise<T>,
  params: UsePromiseWithSnackbarErrorParams
): UsePromiseResponse<T> {
  const res = usePromise(fn, params);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const { errorMessage } = params;

  useEffect(() => {
    if (res.isRejected) {
      enqueueErrorSnackbar(errorMessage, res.error || "");
    }
  }, [enqueueErrorSnackbar, errorMessage, res.error, res.isRejected]);

  return res;
}

export default usePromiseWithSnackbarError;
