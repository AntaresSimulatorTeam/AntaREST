import { ProviderContext, useSnackbar } from "notistack";
import { useCallback } from "react";
import { L } from "ts-toolbelt";
import SnackErrorMessage from "../components/common/SnackErrorMessage";

/**
 * Types
 */

type EnqueueErrorType = ProviderContext["enqueueSnackbar"];

type EnqueueErrorSnackbarType = (
  message: L.Head<Parameters<EnqueueErrorType>>,
  details: string | Error
) => ReturnType<EnqueueErrorType>;

/**
 * Hook
 */

function useEnqueueErrorSnackbar(): EnqueueErrorSnackbarType {
  const { enqueueSnackbar } = useSnackbar();

  return useCallback<EnqueueErrorSnackbarType>(
    (message, details) => {
      return enqueueSnackbar(message, {
        variant: "error",
        persist: true,
        content: (key, msg) => (
          <SnackErrorMessage id={key} message={msg} details={details} />
        ),
      });
    },
    [enqueueSnackbar]
  );
}

export default useEnqueueErrorSnackbar;
