import * as RA from "ramda-adjunct";
import { AutoSubmitConfig, FormProps } from ".";

export function toAutoSubmitConfig(
  value: FormProps["autoSubmit"]
): Required<AutoSubmitConfig> {
  return {
    wait: 2000, // ! Keep 2s while this issue is not fixed: https://github.com/AntaresSimulatorTeam/AntaREST/issues/1050
    ...(RA.isPlainObj(value) ? value : { enable: !!value }),
  };
}

type UnknownArrayOrObject = unknown[] | Record<string, unknown>;

// From https://github.com/react-hook-form/react-hook-form/discussions/1991#discussioncomment-351784
// With little TS fixes.
export function getDirtyValues(
  dirtyFields: UnknownArrayOrObject | true,
  allValues: UnknownArrayOrObject
): UnknownArrayOrObject {
  // NOTE: Recursive function.

  // If *any* item in an array was modified, the entire array must be submitted, because there's no
  // way to indicate "placeholders" for unchanged elements. `dirtyFields` is `true` for leaves.
  if (dirtyFields === true || Array.isArray(dirtyFields)) {
    return allValues;
  }

  // Here, we have an object.
  return Object.fromEntries(
    Object.keys(dirtyFields)
      .filter((key) => dirtyFields[key] !== false)
      .map((key) => [
        key,
        getDirtyValues(
          dirtyFields[key] as UnknownArrayOrObject | true,
          (allValues as Record<string, unknown>)[key] as UnknownArrayOrObject
        ),
      ])
  );
}

// From https://github.com/react-hook-form/react-hook-form/blob/master/src/utils/stringToPath.ts
export function stringToPath(input: string): string[] {
  return input
    .replace(/["|']|\]/g, "")
    .split(/\.|\[/)
    .filter(Boolean);
}
