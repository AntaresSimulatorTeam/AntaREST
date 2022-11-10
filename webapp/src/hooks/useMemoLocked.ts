import { useState } from "react";

/* 
 "You may rely on useMemo as a performance optimization, not as a semantic
 guarantee. In the future, React may choose to “forget” some previously
 memoized values and recalculate them on next render, e.g. to free memory for
 offscreen components. Write your code so that it still works without useMemo —
 and then add it to optimize performance."
 Source: https://reactjs.org/docs/hooks-reference.html#usememo
*/

function useMemoLocked<T>(factory: () => T): T {
  const [state] = useState(factory);
  return state;
}

export default useMemoLocked;
