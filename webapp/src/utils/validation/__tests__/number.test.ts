/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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

import { validateNumber } from "../number";

// Mock i18next
vi.mock("i18next", () => ({
  t: vi.fn((key, options) => {
    if (options) {
      return `${key}: ${JSON.stringify(options)}`;
    }
    return key;
  }),
}));

describe("validateNumber", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should return true for a valid number", () => {
    expect(validateNumber(5)).toBe(true);
  });

  test("should return an error for non-finite numbers", () => {
    expect(validateNumber(NaN)).toBe('form.field.invalidValue: {"value":null}');
    expect(validateNumber(Infinity)).toBe('form.field.invalidValue: {"value":null}');
    expect(validateNumber(-Infinity)).toBe('form.field.invalidValue: {"value":null}');
  });

  test("should handle minimum value validation", () => {
    expect(validateNumber(5, { min: 0 })).toBe(true);
    expect(validateNumber(-1, { min: 0 })).toBe('form.field.minValue: {"0":0}');
  });

  test("should handle maximum value validation", () => {
    expect(validateNumber(5, { max: 10 })).toBe(true);
    expect(validateNumber(11, { max: 10 })).toBe('form.field.maxValue: {"0":10}');
  });

  test("should handle both minimum and maximum value validation", () => {
    expect(validateNumber(5, { min: 0, max: 10 })).toBe(true);
    expect(validateNumber(-1, { min: 0, max: 10 })).toBe('form.field.minValue: {"0":0}');
    expect(validateNumber(11, { min: 0, max: 10 })).toBe('form.field.maxValue: {"0":10}');
  });

  test("should handle integer validation", () => {
    expect(validateNumber(5, { integer: true })).toBe(true);
    expect(validateNumber(5.5, { integer: true })).toBe("form.field.mustBeInteger");
  });

  test("should work with currying", () => {
    const validator = validateNumber({ min: 0, max: 10 });
    expect(validator(5)).toBe(true);
    expect(validator(-1)).toBe('form.field.minValue: {"0":0}');
    expect(validator(11)).toBe('form.field.maxValue: {"0":10}');
  });

  test("should handle extreme values", () => {
    expect(validateNumber(Number.MAX_SAFE_INTEGER)).toBe(true);
    expect(validateNumber(Number.MIN_SAFE_INTEGER)).toBe(true);
  });

  test("should handle custom ranges", () => {
    expect(validateNumber(50, { min: -100, max: 100 })).toBe(true);
    expect(validateNumber(-150, { min: -100, max: 100 })).toBe('form.field.minValue: {"0":-100}');
    expect(validateNumber(150, { min: -100, max: 100 })).toBe('form.field.maxValue: {"0":100}');
  });

  test("should handle decimal numbers", () => {
    expect(validateNumber(3.14)).toBe(true);
    expect(validateNumber(3.14, { min: 3, max: 4 })).toBe(true);
    expect(validateNumber(2.99, { min: 3, max: 4 })).toBe('form.field.minValue: {"0":3}');
  });
});
