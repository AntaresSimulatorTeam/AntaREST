import { History, Transition } from "history";
import { useContext, useEffect } from "react";
import { UNSAFE_NavigationContext as NavigationContext } from "react-router-dom";
import useAutoUpdateRef from "./useAutoUpdateRef";

// * Workaround until it will be supported by react-router v6.
// * Based on https://ui.dev/react-router-preventing-transitions

type Blocker = (tx: Transition) => void;

function useBlocker(blocker: Blocker, when = true): void {
  const { navigator } = useContext(NavigationContext);
  const blockerRef = useAutoUpdateRef(blocker);

  useEffect(
    () => {
      if (!when) {
        return;
      }

      const unblock = (navigator as History).block((tx) => {
        blockerRef.current({
          ...tx,
          retry: (): void => {
            unblock();
            tx.retry();
          },
        });
      });

      return unblock;
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [navigator, when]
  );
}

export default useBlocker;
