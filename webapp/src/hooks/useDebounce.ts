import { debounce, DebouncedFunc, DebounceSettings } from "lodash";
import { useEffect, useMemo, useRef } from "react";
import { F } from "ts-toolbelt";

function useDebounce<T extends F.Function>(
  fn: T,
  wait?: number,
  options?: DebounceSettings
): DebouncedFunc<T> {
  const fnRef = useRef(fn);

  useEffect(() => {
    fnRef.current = fn;
  });

  const debouncedFn = useMemo(
    () => debounce((...args) => fnRef.current(...args), wait, options),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(options), wait]
  );

  useEffect(() => debouncedFn.cancel, [debouncedFn]);

  return debouncedFn;
}

export default useDebounce;
