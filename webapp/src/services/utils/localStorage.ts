
export const loadState = <T>(path: string, defaultValue?: T): T | undefined => {
  try {
    const serializedState = localStorage.getItem(path);
    if (serializedState === null) {
      return defaultValue;
    }
    return JSON.parse(serializedState) as T;
  } catch (err) {
    return defaultValue;
  }
};

export const saveState = <T>(path: string, data: T): void => {
  try {
    const serializedState = JSON.stringify(data);
    localStorage.setItem(path, serializedState);
  } catch {
    // ignore write errors
  }
};
