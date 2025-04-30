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

import type { ValidationReturn } from "@/types/types";
import { t } from "i18next";

interface StringValidationOptions {
  existingValues?: string[];
  excludedValues?: string[];
  isCaseSensitive?: boolean;
  allowSpecialChars?: boolean;
  specialChars?: string;
  allowSpaces?: boolean;
  editedValue?: string;
  minLength?: number;
  maxLength?: number;
}

/**
 * Validates a single string value against specified criteria.
 *
 * Validates the input string against a variety of checks including length restrictions,
 * character validations, and uniqueness against provided arrays of existing and excluded values.
 *
 * @example
 * validateString("foo", { allowSpaces: false }); // true
 * validateNumber("foo bar", { allowSpaces: false }); // Error message
 *
 * @example <caption>With currying.</caption>
 * const fn = validateString({ allowSpaces: false });
 * fn("foo"); // true
 * fn("foo bar"); // Error message
 *
 * @param value - The string to validate. Leading and trailing spaces will be trimmed.
 * @param options - Configuration options for validation. (Optional)
 * @param [options.existingValues=[]] - An array of strings to check against for duplicates. Comparison is case-insensitive by default.
 * @param [options.excludedValues=[]] - An array of strings that the value should not match.
 * @param [options.isCaseSensitive=false] - Whether the comparison with `existingValues` and `excludedValues` is case-sensitive. Defaults to false.
 * @param [options.allowSpecialChars=true] - Flags if special characters are permitted in the value.
 * @param [options.specialChars="&()_-"] - A string representing additional allowed characters outside the typical alphanumeric scope.
 * @param [options.allowSpaces=true] - Flags if spaces are allowed in the value.
 * @param [options.editedValue=""] - The current value being edited, to exclude it from duplicate checks.
 * @param [options.minLength=0] - Minimum length required for the string. Defaults to 0.
 * @param [options.maxLength=255] - Maximum allowed length for the string. Defaults to 255.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validateString(value: string, options?: StringValidationOptions): ValidationReturn;

export function validateString(
  options?: StringValidationOptions,
): (value: string) => ValidationReturn;

export function validateString(
  valueOrOpts?: string | StringValidationOptions,
  options: StringValidationOptions = {},
): ValidationReturn | ((value: string) => ValidationReturn) {
  if (typeof valueOrOpts !== "string") {
    return (v: string) => validateString(v, valueOrOpts);
  }

  const value = valueOrOpts;

  const {
    existingValues = [],
    excludedValues = [],
    isCaseSensitive = false,
    allowSpecialChars = true,
    allowSpaces = true,
    specialChars = "&()_-",
    editedValue = "",
    minLength = 0,
    maxLength = 255,
  } = options;

  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return t("form.field.required");
  }

  if (!allowSpaces && trimmedValue.includes(" ")) {
    return t("form.field.spacesNotAllowed");
  }

  if (trimmedValue.length < minLength) {
    return t("form.field.minLength", { length: minLength });
  }

  if (trimmedValue.length > maxLength) {
    return t("form.field.maxLength", { length: maxLength });
  }

  // Compiles a regex pattern based on allowed characters and flags.
  const specialCharsPattern = new RegExp(
    generatePattern(allowSpaces, allowSpecialChars, specialChars),
  );

  // Validates the string against the allowed characters regex.
  if (!specialCharsPattern.test(trimmedValue)) {
    return specialChars === "" || !allowSpecialChars
      ? t("form.field.specialCharsNotAllowed")
      : t("form.field.specialChars", { 0: specialChars });
  }

  // Normalize the value for comparison, based on case sensitivity option.
  const normalize = (v: string) => (isCaseSensitive ? v.trim() : v.toLowerCase().trim());

  // Prepare the value for duplicate and exclusion checks.
  const comparisonValue = normalize(trimmedValue);

  // Some forms requires to keep the original value while updating other fields.
  if (normalize(editedValue) === comparisonValue) {
    return true;
  }

  // Check for duplication against existing values.
  if (existingValues.map(normalize).includes(comparisonValue)) {
    return t("form.field.duplicate");
  }

  // Check for inclusion in the list of excluded values.
  if (excludedValues.map(normalize).includes(comparisonValue)) {
    return t("form.field.notAllowedValue", { 0: value });
  }

  return true;
}

/**
 * Validates a password string for strong security criteria.
 *
 * @param password - The password to validate.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validatePassword(password: string): ValidationReturn {
  const trimmedPassword = password.trim();

  if (!trimmedPassword) {
    return t("form.field.required");
  }

  if (trimmedPassword.length < 8) {
    return t("form.field.minLength", { length: 8 });
  }

  if (trimmedPassword.length > 50) {
    return t("form.field.maxLength", { length: 50 });
  }

  if (!/[a-z]/.test(trimmedPassword)) {
    return t("form.field.requireLowercase");
  }

  if (!/[A-Z]/.test(trimmedPassword)) {
    return t("form.field.requireUppercase");
  }

  if (!/\d/.test(trimmedPassword)) {
    return t("form.field.requireDigit");
  }

  if (!/[^\w\s]/.test(trimmedPassword)) {
    return t("form.field.requireSpecialChars");
  }

  return true;
}

// Escape special characters in specialChars
function escapeSpecialChars(chars: string) {
  return chars.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&");
}

/**
 * Generates a regular expression pattern for string validation based on specified criteria.
 * This pattern includes considerations for allowing spaces, special characters, and any additional
 * characters specified in `specialChars`.
 *
 * @param allowSpaces - Indicates if spaces are permitted in the string.
 * @param allowSpecialChars - Indicates if special characters are permitted.
 * @param specialChars - Specifies additional characters to allow in the string.
 * @returns The regular expression pattern as a string.
 */
function generatePattern(
  allowSpaces: boolean,
  allowSpecialChars: boolean,
  specialChars: string,
): string {
  const basePattern = "^[a-zA-Z0-9";
  const spacePattern = allowSpaces ? " " : "";
  const specialCharsPattern =
    allowSpecialChars && specialChars ? escapeSpecialChars(specialChars) : "";
  return basePattern + spacePattern + specialCharsPattern + "]*$";
}

interface PathValidationOptions {
  allowToStartWithSlash?: boolean;
  allowToEndWithSlash?: boolean;
  allowEmpty?: boolean;
}

/**
 * Validates a path against specified criteria.
 *
 * @example
 * validatePath("foo/bar", { allowToEndWithSlash: false }); // true
 * validatePath("foo/bar/", { allowToEndWithSlash: false }); // Error message
 *
 * @example <caption>With currying.</caption>
 * const fn = validateString({ allowToEndWithSlash: false });
 * fn("foo/bar"); // true
 * fn("foo/bar/"); // Error message
 *
 * @param path - The string to validate.
 * @param options - Configuration options for validation. (Optional)
 * @param [options.allowToStartWithSlash=true] - Indicates if the path is allowed to start with a '/'.
 * @param [options.allowToEndWithSlash=true] - Indicates if the path is allowed to end with a '/'.
 * @param [options.allowEmpty=false] - Indicates if an empty path is allowed.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validatePath(path: string, options?: PathValidationOptions): ValidationReturn;

export function validatePath(options?: PathValidationOptions): (value: string) => ValidationReturn;

export function validatePath(
  pathOrOpts?: string | PathValidationOptions,
  options: PathValidationOptions = {},
): ValidationReturn | ((value: string) => ValidationReturn) {
  if (typeof pathOrOpts !== "string") {
    return (v: string) => validatePath(v, pathOrOpts);
  }

  const path = pathOrOpts;

  const { allowToStartWithSlash = true, allowToEndWithSlash = true, allowEmpty = false } = options;

  if (!path) {
    return allowEmpty ? true : t("form.field.required");
  }

  if (!allowToStartWithSlash && path.startsWith("/")) {
    return t("form.field.path.startWithSlashNotAllowed");
  }

  if (!allowToEndWithSlash && path.endsWith("/")) {
    return t("form.field.path.endWithSlashNotAllowed");
  }

  if (
    path
      .replace(/^\//, "") // Remove first "/" if present
      .replace(/\/$/, "") // Remove last "/" if present
      .split("/")
      .map((v) => v.trim())
      .includes("")
  ) {
    return t("form.field.path.invalid");
  }

  return true;
}
