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

import type { L } from "ts-toolbelt";
import i18n, { type SUPPORTED_LANGUAGES } from "../i18n";

type Lang = L.UnionOf<typeof SUPPORTED_LANGUAGES>;

/**
 * Gets the current language used in the application.
 *
 * @returns The current language.
 */
export function getCurrentLanguage() {
  return i18n.languages[0] as Lang;
}

/**
 * Changes the language used in the application.
 * The value is automatically saved in the local storage.
 *
 * @param lang - The language to change to.
 * @returns A promise that resolves when the language has been loaded.
 */
export function changeLanguage(lang: Lang) {
  return new Promise<void>((resolve, reject) => {
    i18n.changeLanguage(lang, (err) => {
      err ? reject(err) : resolve();
    });
  });
}

/**
 * Appends a colon (:) at the end with the appropriate spacing for the current language.
 *
 * @param text - The text.
 * @returns The text with a colon (:) appended.
 */
export function translateWithColon(text: string): string {
  return `${text}${i18n.language.startsWith("fr") ? " " : ""}:`;
}
