import * as R from "ramda";
import * as RA from "ramda-adjunct";
import { useEffect } from "react";
import useDebounce, { UseDebounceParams } from "./useDebounce";

export interface UseDebouncedEffectParams extends UseDebounceParams {
  deps?: React.DependencyList;
}

type DepsOrWaitOrParams =
  | React.DependencyList
  | number
  | UseDebouncedEffectParams;

const toParams = R.cond<
  [DepsOrWaitOrParams | undefined],
  UseDebouncedEffectParams
>([
  [RA.isPlainObj, R.identity as () => UseDebouncedEffectParams],
  [RA.isNumber, R.objOf("wait") as () => UseDebouncedEffectParams],
  [RA.isArray, R.objOf("deps") as () => UseDebouncedEffectParams],
  [R.T, RA.stubObj],
]);

function useDebouncedEffect(
  effect: VoidFunction,
  params?: DepsOrWaitOrParams
): void {
  const { deps, ...debounceParams } = toParams(params);
  const debouncedFn = useDebounce(effect, debounceParams);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(debouncedFn, deps);
}

export default useDebouncedEffect;
