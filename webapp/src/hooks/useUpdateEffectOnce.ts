import { useEffect, useRef } from "react";
import { useUpdateEffect } from "react-use";

/**
 * Hook that runs the effect only at the first dependencies update.
 * It behaves like the `useEffect` hook, but it skips the initial run,
 * and the runs following the first update.
 *
 * @param effect - The effect function to run.
 * @param deps - An array of dependencies to watch for changes.
 */
const useUpdateEffectOnce: typeof useEffect = (effect, deps) => {
  const hasUpdated = useRef(false);

  useUpdateEffect(() => {
    if (!hasUpdated.current) {
      hasUpdated.current = true;
      return effect();
    }
  }, deps);
};

export default useUpdateEffectOnce;
