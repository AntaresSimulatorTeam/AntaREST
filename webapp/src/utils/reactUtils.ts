import { setRef } from "@mui/material";
import React from "react";

export function isDependencyList(
  value: unknown
): value is React.DependencyList {
  return Array.isArray(value);
}

export function composeRefs(...refs: React.Ref<unknown>[]) {
  return function refCallback(instance: unknown): void {
    refs.forEach((ref) => setRef(ref, instance));
  };
}
