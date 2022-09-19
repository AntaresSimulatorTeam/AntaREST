import useBlocker from "./useBlocker";

// * Workaround until it will be supported by react-router v6.
// * Based on https://ui.dev/react-router-preventing-transitions

function usePrompt(message: string, when = true): void {
  useBlocker((tx) => {
    // eslint-disable-next-line no-alert
    if (window.confirm(message)) {
      tx.retry();
    }
  }, when);
}

export default usePrompt;
