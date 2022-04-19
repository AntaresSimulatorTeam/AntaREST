import { SnackbarKey, SnackbarMessage, useSnackbar } from "notistack";
import { useMemo } from "react";
import enqueueErrorSnackbar from "../components/common/ErrorSnackBar";

/**
 * Types
 */

type Fn = (message: SnackbarMessage, details: string | Error) => SnackbarKey;

/**
 * Hook
 */

function useEnqueueErrorSnackbar(): Fn {
  const { enqueueSnackbar } = useSnackbar();

  return useMemo(
    () => enqueueErrorSnackbar.bind(null, enqueueSnackbar),
    [enqueueSnackbar]
  );
}

export default useEnqueueErrorSnackbar;
