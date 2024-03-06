import { t } from "i18next";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

interface ValidationOptions {
  existingValues?: string[];
  excludedValues?: string[];
  isCaseSensitive?: boolean;
  allowSpecialChars?: boolean;
  allowedChars?: string;
  allowSpaces?: boolean;
  editedValue?: string;
  min?: number;
  max?: number;
}

////////////////////////////////////////////////////////////////
// Validators
////////////////////////////////////////////////////////////////

/**
 * Validates a single string value against specified criteria.
 *
 * Validates the input string against a variety of checks including length restrictions,
 * character validations, and uniqueness against provided arrays of existing and excluded values.
 *
 * @param value - The string to validate. Leading and trailing spaces will be trimmed.
 * @param options - Configuration options for validation.
 * @param options.existingValues - An array of strings to check against for duplicates. Comparison is case-insensitive by default.
 * @param options.excludedValues - An array of strings that the value should not match.
 * @param options.isCaseSensitive - Whether the comparison with `existingValues` and `excludedValues` is case-sensitive. Defaults to false.
 * @param options.allowSpecialChars - Flags if special characters are permitted in the value.
 * @param options.allowedChars - A string representing additional allowed characters outside the typical alphanumeric scope.
 * @param options.allowSpaces - Flags if spaces are allowed in the value.
 * @param options.editedValue - The current value being edited, to exclude it from duplicate checks.
 * @param options.min - Minimum length required for the string. Defaults to 0.
 * @param options.max - Maximum allowed length for the string. Defaults to 255.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validateString(
  value: string,
  options?: ValidationOptions,
): string | true {
  const {
    existingValues = [],
    excludedValues = [],
    isCaseSensitive = false,
    allowSpecialChars = true,
    allowSpaces = true,
    allowedChars = "&()_-",
    editedValue = "",
    min = 0,
    max = 255,
  } = options || {};

  const trimmedValue = value.trim();

  if (!trimmedValue) {
    return t("form.field.required");
  }

  if (!allowSpaces && trimmedValue.includes(" ")) {
    return t("form.field.spacesNotAllowed");
  }

  if (trimmedValue.length < min) {
    return t("form.field.minValue", { 0: min });
  }

  if (trimmedValue.length > max) {
    return t("form.field.maxValue", { 0: max });
  }

  // Compiles a regex pattern based on allowed characters and flags.
  const allowedCharsPattern = new RegExp(
    generatePattern(allowSpaces, allowSpecialChars, allowedChars),
  );

  // Validates the string against the allowed characters regex.
  if (!allowedCharsPattern.test(trimmedValue)) {
    return allowSpecialChars
      ? t("form.field.allowedChars", { 0: allowedChars })
      : t("form.field.specialCharsNotAllowed");
  }

  // Normalize the value for comparison, based on case sensitivity option.
  const normalize = (v: string) =>
    isCaseSensitive ? v.trim() : v.toLowerCase().trim();

  // Prepare the value for duplicate and exclusion checks.
  const comparisonValue = normalize(trimmedValue);

  // Some forms requires to keep the original value while updating other fields.
  if (normalize(editedValue) === comparisonValue) {
    return true;
  }

  // Check for duplication against existing values.
  if (existingValues.map(normalize).includes(comparisonValue)) {
    return t("form.field.duplicate", { 0: value });
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
 * @param confirmPassword - An optional second password to compare against the first for matching.
 * @returns True if validation is successful, or a localized error message if it fails.
 */
export function validatePassword(
  password: string,
  confirmPassword?: string,
): string | true {
  const trimmedPassword = password.trim();

  if (!trimmedPassword) {
    return t("form.field.required");
  }

  if (!/(?=.*[a-z])/.test(trimmedPassword)) {
    return t("form.field.requireLowercase");
  }

  if (!/(?=.*[A-Z])/.test(trimmedPassword)) {
    return t("form.field.requireUppercase");
  }

  if (!/(?=.*\d)/.test(trimmedPassword)) {
    return t("form.field.requireDigit");
  }

  if (!/(?=.*[^\w\s])/.test(trimmedPassword)) {
    return t("form.field.requireSpecialChars");
  }

  if (trimmedPassword.length < 8) {
    return t("form.field.minValue", { 0: 8 });
  }

  if (trimmedPassword.length > 30) {
    return t("form.field.maxValue", { 0: 30 });
  }

  if (
    confirmPassword !== undefined &&
    trimmedPassword !== confirmPassword.trim()
  ) {
    return t("settings.error.passwordMismatch");
  }

  return true;
}

////////////////////////////////////////////////////////////////
// Utils
////////////////////////////////////////////////////////////////

// Function to escape special characters in allowedChars
const escapeSpecialChars = (chars: string) =>
  chars.replace(/[-\\^$*+?.()|[\]{}]/g, "\\$&");

/**
 * Generates a regular expression pattern for string validation based on specified criteria.
 * This pattern includes considerations for allowing spaces, special characters, and any additional
 * characters specified in `allowedChars`.
 *
 * @param allowSpaces - Indicates if spaces are permitted in the string.
 * @param allowSpecialChars - Indicates if special characters are permitted.
 * @param allowedChars - Specifies additional characters to allow in the string.
 * @returns The regular expression pattern as a string.
 */
function generatePattern(
  allowSpaces: boolean,
  allowSpecialChars: boolean,
  allowedChars: string,
): string {
  const basePattern = "^[a-zA-Z0-9";
  const spacePattern = allowSpaces ? " " : "";
  const specialCharsPattern =
    allowSpecialChars && allowedChars ? escapeSpecialChars(allowedChars) : "";
  return basePattern + spacePattern + specialCharsPattern + "]*$";
}
