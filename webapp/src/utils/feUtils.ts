import { HTMLInputTypeAttribute } from "react";

export interface FakeHTMLInputElement {
  value: unknown;
  type?: HTMLInputTypeAttribute;
  name?: string;
}

type Target = HTMLInputElement | FakeHTMLInputElement;

export interface FakeChangeEventHandler {
  target: Target;
  type: "change";
}

export interface FakeBlurEventHandler {
  target: Target;
  type: "blur";
}

export function createFakeChangeEventHandler(
  target: Target
): FakeChangeEventHandler {
  return {
    target,
    type: "change",
  };
}

export function createFakeBlurEventHandler(
  target: Target
): FakeBlurEventHandler {
  return {
    target,
    type: "blur",
  };
}
