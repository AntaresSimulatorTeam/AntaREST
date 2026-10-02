/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { createElement, forwardRef, memo } from "react";
import { getChildKey, isValidSizes } from "../utils";

describe("SplitView utils", () => {
  describe("isValidSizes", () => {
    test("should return true for valid sizes array summing to 100", () => {
      expect(isValidSizes([50, 50])).toBe(true);
      expect(isValidSizes([25, 75])).toBe(true);
      expect(isValidSizes([10, 30, 60])).toBe(true);
      expect(isValidSizes([33.33, 33.33, 33.34])).toBe(true);
    });

    test("should return false for arrays not summing to 100", () => {
      expect(isValidSizes([50, 40])).toBe(false);
      expect(isValidSizes([60, 60])).toBe(false);
      expect(isValidSizes([25, 25, 25])).toBe(false);
    });

    test("should return false for non-array values", () => {
      expect(isValidSizes(null)).toBe(false);
      expect(isValidSizes(undefined)).toBe(false);
      expect(isValidSizes("50,50")).toBe(false);
      expect(isValidSizes({ a: 50, b: 50 })).toBe(false);
      expect(isValidSizes(100)).toBe(false);
    });

    test("should return false for arrays with non-numeric values", () => {
      expect(isValidSizes([50, "50"])).toBe(false);
      expect(isValidSizes([50, null])).toBe(false);
      expect(isValidSizes([50, undefined])).toBe(false);
    });

    test("should return false for empty array", () => {
      expect(isValidSizes([])).toBe(false);
    });
  });

  describe("getChildKey", () => {
    test("should return generic key for non-element children", () => {
      expect(getChildKey(null, 0)).toBe("split-child-0");
      expect(getChildKey(undefined, 1)).toBe("split-child-1");
      expect(getChildKey("text", 2)).toBe("split-child-2");
      expect(getChildKey(123, 3)).toBe("split-child-3");
    });

    test("should use existing key if present", () => {
      const element = createElement("div", { key: "custom-key" });
      expect(getChildKey(element, 0)).toBe("custom-key");
    });

    test("should generate key from DOM element type", () => {
      const divElement = createElement("div", null);
      expect(getChildKey(divElement, 0)).toBe("split-div-0");

      const spanElement = createElement("span", null);
      expect(getChildKey(spanElement, 1)).toBe("split-span-1");
    });

    test("should generate key from function component name", () => {
      function MyComponent() {
        return createElement("div");
      }

      const element = createElement(MyComponent);
      expect(getChildKey(element, 0)).toBe("split-MyComponent-0");
    });

    test("should handle anonymous function components", () => {
      const AnonymousComponent = () => createElement("div");
      // Anonymous functions may have empty name
      const element = createElement(AnonymousComponent);
      const key = getChildKey(element, 0);
      // Key should start with "split-" and end with "-0"
      expect(key).toMatch(/^split-.+-0$/);
    });

    test("should handle different indices correctly", () => {
      const element1 = createElement("div");
      const element2 = createElement("div");

      expect(getChildKey(element1, 0)).toBe("split-div-0");
      expect(getChildKey(element2, 5)).toBe("split-div-5");
    });

    test("should handle memo components", () => {
      function MyComponent() {
        return createElement("div");
      }
      const MemoComponent = memo(MyComponent);

      const element = createElement(MemoComponent);
      const key = getChildKey(element, 0);
      // Memo components might have different type structure
      expect(key).toMatch(/^split-.+-0$/);
    });

    test("should handle forwardRef components", () => {
      const ForwardRefComponent = forwardRef(function ForwardRefTestComponent() {
        return createElement("div");
      });

      const element = createElement(ForwardRefComponent);
      const key = getChildKey(element, 0);
      // ForwardRef components might have different type structure
      expect(key).toMatch(/^split-.+-0$/);
    });

    test("should generate different keys for different component types at same index", () => {
      function ComponentA() {
        return createElement("div");
      }
      function ComponentB() {
        return createElement("div");
      }

      const elementA = createElement(ComponentA);
      const elementB = createElement(ComponentB);

      const keyA = getChildKey(elementA, 0);
      const keyB = getChildKey(elementB, 0);

      expect(keyA).not.toBe(keyB);
      expect(keyA).toBe("split-ComponentA-0");
      expect(keyB).toBe("split-ComponentB-0");
    });

    test("should generate same key for same component type at same index", () => {
      function MyComponent() {
        return createElement("div");
      }

      const element1 = createElement(MyComponent);
      const element2 = createElement(MyComponent);

      expect(getChildKey(element1, 0)).toBe(getChildKey(element2, 0));
    });

    test("should handle components with displayName", () => {
      function MyComponent() {
        return createElement("div");
      }
      MyComponent.displayName = "CustomDisplayName";

      const element = createElement(MyComponent);
      const key = getChildKey(element, 0);
      expect(key).toMatch(/^split-.+-0$/);
    });
  });
});
