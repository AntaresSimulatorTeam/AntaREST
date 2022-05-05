import { DependencyList, useCallback, useEffect, useState } from "react";

export interface UsePromiseResponse<T> {
  data: T | undefined;
  isLoading: boolean;
  error: Error | string | undefined;
  reload: () => void;
}

function usePromise<T>(
  fn: () => Promise<T>,
  deps: DependencyList = []
): UsePromiseResponse<T> {
  const [data, setData] = useState<T>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | string | undefined>();
  const [reloadCount, setReloadCount] = useState(0);
  const reload = useCallback(() => setReloadCount((prev) => prev + 1), []);

  useEffect(
    () => {
      let isMounted = true;

      setIsLoading(true);
      // Reset
      setData(undefined);
      setError(undefined);

      fn()
        .then((res) => {
          if (isMounted) {
            setData(res);
          }
        })
        .catch((err) => {
          if (isMounted) {
            setError(err);
          }
        })
        .finally(() => {
          if (isMounted) {
            setIsLoading(false);
          }
        });

      return () => {
        isMounted = false;
      };
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [reloadCount, ...deps]
  );

  return { data, isLoading, error, reload };
}

export default usePromise;
