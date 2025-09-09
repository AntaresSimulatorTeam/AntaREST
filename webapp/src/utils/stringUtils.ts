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

import deburr from "lodash/deburr";
import * as R from "ramda";
import * as RA from "ramda-adjunct";

export const isSearchMatching = R.curry((search: string, values: string | string[]) => {
  const format = R.o(R.toLower, deburr);
  const isMatching = R.o(R.includes(format(search)), format);
  return RA.ensureArray(values).find(isMatching);
});

/**
 * Formats a string by replacing placeholders with specified values.
 *
 * @param str - The string containing placeholders in the format `{placeholder}`.
 * @param values - An object mapping placeholders to their replacement values.
 * Each value are stringified before replacement.
 * @returns The formatted string with all placeholders replaced by their corresponding values.
 *
 * @example
 * format("Hello {name}", { name: "John" }); // Returns: "Hello John"
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function format(str: string, values: Record<string, any>): string {
  return str.replace(/{([a-zA-Z0-9]+)}/g, (_, key) => String(values[key]));
}
