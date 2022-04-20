import { DependencyList, useEffect } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "./useEnqueueErrorSnackbar";
import usePromise, { UsePromiseResponse } from "./usePromise";

function usePromiseWithSnackbarError<T>(
  fn: () => Promise<T>,
  errorMessageKey: string,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const res = usePromise(fn, deps);
  const { enqueueSnackbar } = useSnackbar();
  const [t] = useTranslation();

  useEffect(
    () => {
      if (res.error) {
        enqueueErrorSnackbar(enqueueSnackbar, t(errorMessageKey), res.error);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [res.error]
  );

  return res;
}

export default usePromiseWithSnackbarError;
