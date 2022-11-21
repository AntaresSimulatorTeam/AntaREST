import { DefaultValues, FieldValues } from "react-hook-form";
import usePromiseWithSnackbarError from "../../../hooks/usePromiseWithSnackbarError";
import { UseFormPropsPlus } from "./types";

function useAsyncDefaultValues<TFieldValues extends FieldValues>(
  fn: UseFormPropsPlus<TFieldValues>["asyncDefaultValues"],
  onResolve: (defaultValues: DefaultValues<TFieldValues>) => void
): void {
  usePromiseWithSnackbarError(
    async () => {
      if (fn) {
        const data = await fn();
        onResolve(data);
      }
    },
    { errorMessage: "Cannot get form fields" }
  );
}

export default useAsyncDefaultValues;
