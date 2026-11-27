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

const KEYBOARD_EQUIVALENTS: Record<string, string> = {
  "→": "->",
  "➔": "->",
  "➜": "->",
  "←": "<-",
  "⇒": "=>",
  "⇐": "<=",
  "↔": "<->",
  "✓": "[OK]",
  "✔": "[OK]",
  "✅": "[OK]",
  "☑": "[OK]",
  "✗": "[X]",
  "✘": "[X]",
  "✖": "[X]",
  "❌": "[X]",
  "├": "|",
  "│": "|",
  "└": "`",
  "─": "-",
  " ": " ",
};

const REPLACEABLE_CHARACTERS = new RegExp(Object.keys(KEYBOARD_EQUIVALENTS).join("|"), "gu");

const PICTOGRAMS = String.raw`(?:(?![©®™])[\p{Extended_Pictographic}\p{Emoji_Modifier}\p{Regional_Indicator}][️‍]*)+`;

const PICTOGRAMS_ENDING_A_LINE = new RegExp(String.raw`[ \t]*${PICTOGRAMS}[ \t]*$`, "gmu");

const PICTOGRAMS_INSIDE_A_LINE = new RegExp(String.raw`${PICTOGRAMS}[ \t]*`, "gu");

/**
 * Rewrites a text so that the font embedded in the PDF (Roboto) can draw all of it: the AI
 * assistant often writes arrows, check marks and pictograms, which this font does not have and
 * which would be printed as empty boxes.
 *
 * @param text - Text to write in the PDF.
 * @returns The text with arrows, marks and tree lines written with keyboard characters, and
 * without pictograms.
 */
export function sanitizePdfText(text: string): string {
  return text
    .replace(REPLACEABLE_CHARACTERS, (character) => KEYBOARD_EQUIVALENTS[character])
    .replace(PICTOGRAMS_ENDING_A_LINE, "")
    .replace(PICTOGRAMS_INSIDE_A_LINE, "");
}
