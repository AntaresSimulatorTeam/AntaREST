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

const SIZE_UNITS = ["bytes", "kb", "mb", "gb", "tb", "pb"] as const;

/**
 * Formats a byte count with decimal units in the current application language.
 *
 * @param bytes - The byte count to format.
 * @returns The localized size and unit.
 */
export function formatBytes(bytes: number): string {
  const exponent = bytes > 0 ? Math.floor(Math.log(bytes) / Math.log(1000)) : 0;
  const unitIndex = Math.max(0, Math.min(exponent, SIZE_UNITS.length - 1));
  const value = new Intl.NumberFormat(i18n.resolvedLanguage ?? i18n.language, {
    maximumFractionDigits: 1,
  }).format(bytes / 1000 ** unitIndex);

  return i18n.t(`global.units.${SIZE_UNITS[unitIndex]}`, { value });
}
