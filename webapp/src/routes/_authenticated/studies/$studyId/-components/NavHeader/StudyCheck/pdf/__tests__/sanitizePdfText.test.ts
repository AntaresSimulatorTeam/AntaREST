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

import { sanitizePdfText } from "../sanitizePdfText";

describe("sanitizePdfText", () => {
  test("keeps the text the font of the PDF can draw", () => {
    const text = "Coût « élevé » : 1 500 € ≥ 180 EUR/MWh – œuvre, x² ≠ y…";

    expect(sanitizePdfText(text)).toBe(text);
  });

  test("writes arrows with the characters of the keyboard", () => {
    expect(sanitizePdfText("fr → de, de ← fr, a ⇒ b, a ↔ b")).toBe(
      "fr -> de, de <- fr, a => b, a <-> b",
    );
  });

  test("writes check marks and crosses as words", () => {
    expect(sanitizePdfText("✅ thermal ✓ hydro ❌ links ✗ storages")).toBe(
      "[OK] thermal [OK] hydro [X] links [X] storages",
    );
  });

  test("removes the pictograms, with the space which follows them", () => {
    expect(sanitizePdfText("⚠️ Attention : 🔴 erreur bloquante 🚀")).toBe(
      "Attention : erreur bloquante",
    );
  });

  test("keeps the digits of a number together when they are separated by a narrow space", () => {
    expect(sanitizePdfText("1\u202F500 MW")).toBe("1\u00A0500 MW");
  });

  test("draws the lines of a tree with the characters of the keyboard", () => {
    expect(sanitizePdfText("├── input\n│   └── links")).toBe("|-- input\n|   `-- links");
  });
});
