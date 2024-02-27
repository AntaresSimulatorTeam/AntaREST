import { HTMLInputTypeAttribute } from "react";

export interface InputObject {
  value: unknown;
  checked?: boolean;
  type?: HTMLInputTypeAttribute;
  name?: string;
}

type Target = HTMLInputElement | InputObject;

export interface FakeChangeEventHandler {
  target: Target;
  type: "change";
}

export interface FakeBlurEventHandler {
  target: Target;
  type: "blur";
}

export function createFakeChangeEventHandler(
  target: Target,
): FakeChangeEventHandler {
  return {
    target,
    type: "change",
  };
}

export function createFakeBlurEventHandler(
  target: Target,
): FakeBlurEventHandler {
  return {
    target,
    type: "blur",
  };
}

export function createFakeInputElement(obj: InputObject): HTMLInputElement {
  const inputElement = document.createElement("input");
  inputElement.name = obj.name || "";
  inputElement.value = obj.value as string;

  return inputElement;
}
