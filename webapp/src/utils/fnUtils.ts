/**
 * Use it instead of disabling ESLint rule.
 */
export function voidFn<TArgs extends unknown[]>(...args: TArgs) {
  // Do nothing
}

/**
 * A utility function that converts an unknown value to an Error object.
 * If the value is already an Error object, it is returned as is.
 * If the value is a string, it is used as the message for the new Error object.
 * If the value is anything else, a new Error object with a generic message is created.
 *
 * @param error - The value to convert to an Error object.
 * @returns An Error object.
 */
export function toError(error: unknown) {
  if (error instanceof Error) {
    return error;
  }
  if (typeof error === "string") {
    return new Error(error);
  }
  return new Error("An unknown error occurred");
}
