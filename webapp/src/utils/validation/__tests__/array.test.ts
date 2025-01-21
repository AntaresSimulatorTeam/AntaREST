/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { validateArray } from "../array";

vi.mock("i18next", () => ({
  t: vi.fn((key) => key),
}));

describe("validateArray", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should return true for a non-empty array with no duplicates", () => {
    expect(validateArray([1, 2, 3])).toBe(true);
  });

  test("should return an error message for an empty array when not allowed", () => {
    expect(validateArray([])).toBe("form.field.required");
  });

  test("should return true for an empty array when allowed", () => {
    expect(validateArray([], { allowEmpty: true })).toBe(true);
  });

  test("should return an error message for an array with duplicates when not allowed", () => {
    expect(validateArray([1, 2, 2, 3])).toBe("form.field.duplicateNotAllowed");
  });

  test("should return true for an array with duplicates when allowed", () => {
    expect(validateArray([1, 2, 2, 3], { allowDuplicate: true })).toBe(true);
  });

  test("should work with currying", () => {
    const validator = validateArray({ allowDuplicate: false });
    expect(validator([1, 2, 3])).toBe(true);
    expect(validator([1, 1, 2, 3])).toBe("form.field.duplicateNotAllowed");
  });

  test("should work with different types of array elements", () => {
    expect(validateArray(["a", "b", "c"])).toBe(true);
    expect(validateArray([{ id: 1 }, { id: 2 }])).toBe(true);
  });

  test("should handle both options simultaneously", () => {
    expect(validateArray([], { allowEmpty: true, allowDuplicate: false })).toBe(true);
    expect(validateArray([1, 1], { allowEmpty: true, allowDuplicate: true })).toBe(true);
    expect(validateArray([1, 1], { allowEmpty: true, allowDuplicate: false })).toBe(
      "form.field.duplicateNotAllowed",
    );
  });
});
