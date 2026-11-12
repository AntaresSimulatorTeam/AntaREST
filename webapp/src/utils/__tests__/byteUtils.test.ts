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

import i18n from "@/i18n";
import en from "../../../public/locales/en/main.json";
import fr from "../../../public/locales/fr/main.json";
import { formatBytes } from "../byteUtils";

beforeAll(async () => {
  await i18n.init({
    lng: "en",
    resources: { en: { main: en }, fr: { main: fr } },
  });
});

test.each([
  ["en", 999, "999 B"],
  ["en", 1000, "1 KB"],
  ["en", 1.5 * 1000 ** 3, "1.5 GB"],
  ["fr", 1.5 * 1000 ** 3, "1,5 Go"],
])("formats %s byte counts using decimal units: %s", async (language, bytes, expected) => {
  await i18n.changeLanguage(language);

  expect(formatBytes(bytes)).toBe(expected);
});
