import {
  DebouncedFunc,
  DebouncedFuncLeading,
  DebounceSettingsLeading,
} from "lodash";
import { useState } from "react";
import useDebounce, { UseDebounceParams } from "./useDebounce";

type WaitOrParams = number | UseDebounceParams;

type DebounceFn<S> = (state: S) => void;

type UseDebouncedStateReturn<S, U extends WaitOrParams> = [
  S,
  U extends DebounceSettingsLeading
    ? DebouncedFuncLeading<DebounceFn<S>>
    : DebouncedFunc<DebounceFn<S>>
];

function useDebouncedState<S, U extends WaitOrParams = WaitOrParams>(
  initialValue: S | (() => S),
  params?: U
): UseDebouncedStateReturn<S, U> {
  const [state, setState] = useState(initialValue);

  const debounceFn = useDebounce((newState) => {
    setState(newState);
  }, params);

  return [state, debounceFn];
}

export default useDebouncedState;
