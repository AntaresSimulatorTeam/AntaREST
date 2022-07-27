import { useEffect, useRef } from "react";

function useAutoUpdateRef<T>(value: T): React.MutableRefObject<T> {
  const ref = useRef(value);

  useEffect(() => {
    ref.current = value;
  });

  return ref;
}

export default useAutoUpdateRef;
