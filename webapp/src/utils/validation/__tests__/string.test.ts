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

import { validatePassword, validateString } from "../string";

vi.mock("i18next", () => ({
  t: vi.fn((key, options) => {
    if (options) {
      return `${key}: ${JSON.stringify(options)}`;
    }
    return key;
  }),
}));

describe("validateString", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should return true for a valid string", () => {
    expect(validateString("Valid String")).toBe(true);
  });

  test("should return an error for an empty string", () => {
    expect(validateString("")).toBe("form.field.required");
    expect(validateString("   ")).toBe("form.field.invalidValue");
  });

  test("should handle length restrictions", () => {
    expect(validateString("abc", { minLength: 5 })).toBe('form.field.minLength: {"length":5}');
    expect(validateString("abcdefghijk", { maxLength: 10 })).toBe(
      'form.field.maxLength: {"length":10}',
    );
  });

  test("should handle space restrictions", () => {
    expect(validateString("no spaces", { allowSpaces: false })).toBe("form.field.spacesNotAllowed");
  });

  test("should handle special character restrictions", () => {
    expect(validateString("abc123!@#", { allowSpecialChars: false })).toBe(
      "form.field.specialCharsNotAllowed",
    );
    expect(
      validateString("abc123!@#", {
        allowSpecialChars: true,
        specialChars: "!@#",
      }),
    ).toBe(true);
    expect(
      validateString("abc123$%^", {
        allowSpecialChars: true,
        specialChars: "!@#",
      }),
    ).toBe('form.field.specialCharsAllowedList: {"chars":"!@#"}');
    expect(
      validateString("abc123!@#", {
        allowSpecialChars: true,
        specialChars: { chars: "?&", mode: "deny" },
      }),
    ).toBe(true);
    expect(
      validateString("abc123!@#", {
        allowSpecialChars: true,
        specialChars: { chars: "!@#", mode: "deny" },
      }),
    ).toBe('form.field.specialCharsNotAllowedList: {"chars":"!@#"}');
  });

  test("should handle duplicate checks", () => {
    expect(validateString("existing", { existingValues: ["EXISTING", "other"] })).toBe(
      "form.field.duplicate",
    );
    expect(
      validateString("existing", {
        existingValues: ["EXISTING", "other"],
        isCaseSensitive: true,
      }),
    ).toBe(true);
  });

  test("should handle excluded values", () => {
    expect(validateString("excluded", { excludedValues: ["EXCLUDED", "other"] })).toBe(
      'form.field.notAllowedValue: {"0":"excluded"}',
    );
    expect(
      validateString("excluded", {
        excludedValues: ["EXCLUDED", "other"],
        isCaseSensitive: true,
      }),
    ).toBe(true);
  });

  test("should ignore the edited value in duplicate checks", () => {
    expect(
      validateString("existing", {
        existingValues: ["existing", "other"],
        editedValue: "existing",
      }),
    ).toBe(true);
  });
});

describe("validatePassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should return true for a valid password", () => {
    expect(validatePassword("ValidP@ssw0rd")).toBe(true);
  });

  test("should return an error for an empty password", () => {
    expect(validatePassword("")).toBe("form.field.required");
    expect(validatePassword("   ")).toBe("form.field.required");
  });

  test("should check minimum length", () => {
    expect(validatePassword("Short1!")).toBe('form.field.minLength: {"length":8}');
  });

  test("should check maximum length", () => {
    expect(validatePassword("A".repeat(51) + "a1!")).toBe('form.field.maxLength: {"length":50}');
  });

  test("should require lowercase letters", () => {
    expect(validatePassword("UPPERCASE123!")).toBe("form.field.requireLowercase");
  });

  test("should require uppercase letters", () => {
    expect(validatePassword("lowercase123!")).toBe("form.field.requireUppercase");
  });

  test("should require digits", () => {
    expect(validatePassword("UpperAndLowercase!")).toBe("form.field.requireDigit");
  });

  test("should require special characters", () => {
    expect(validatePassword("UpperAndLowercase123")).toBe("form.field.requireSpecialChars");
  });
});
