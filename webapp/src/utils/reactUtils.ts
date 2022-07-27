import { setRef } from "@mui/material";

export function isDependencyList(
  value: unknown
): value is React.DependencyList {
  return Array.isArray(value);
}

export function composeRefs(
  ...refs: Array<React.Ref<unknown> | undefined | null>
) {
  return function refCallback(instance: unknown): void {
    refs.forEach((ref) => setRef(ref, instance));
  };
}

export function getComponentDisplayName<T>(
  comp: React.ComponentType<T>
): string {
  return comp.displayName || comp.name || "Component";
}
