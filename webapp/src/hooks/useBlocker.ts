import { History, Transition } from "history";
import { useContext, useEffect, useRef } from "react";
import { UNSAFE_NavigationContext as NavigationContext } from "react-router-dom";

// * Workaround until it will be supported by react-router v6.
// * Based on https://ui.dev/react-router-preventing-transitions

type Blocker = (tx: Transition) => void;

function useBlocker(blocker: Blocker, when = true): void {
  const { navigator } = useContext(NavigationContext);
  const blockerRef = useRef(blocker);

  useEffect(() => {
    blockerRef.current = blocker;
  });

  useEffect(() => {
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
  }, [navigator, when]);
}

export default useBlocker;
