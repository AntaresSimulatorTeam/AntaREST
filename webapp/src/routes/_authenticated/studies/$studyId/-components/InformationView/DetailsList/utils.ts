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

const BYTES_PER_KB = 1024; // 1KB = 1024 bytes
const BYTES_PER_GB = BYTES_PER_KB ** 3; // 1GB = 1024^3 bytes

export const convertSize = (bytes: number): string => {
  const units = ["bytes", "KB", "MB", "GB", "TB"];

  if (bytes < BYTES_PER_KB) {
    return `${bytes} ${units[0]}`;
  }

  let unitIndex = 0;
  let size = bytes;

  while (size >= BYTES_PER_KB && unitIndex < units.length - 1) {
    size /= BYTES_PER_KB;
    unitIndex += 1;
  }

  return `${size.toFixed(2)} ${units[unitIndex]}`;
};

const sizeRanges = [
  { limit: 0, color: "default" }, // Size is unknown or not calculated
  { limit: 5 * BYTES_PER_GB, color: "success.main" }, // Size is 0 to 5 GB
  { limit: 25 * BYTES_PER_GB, color: "warning.main" }, // Size is 5 GB to 25 GB
  { limit: Infinity, color: "error.main" }, // Size is 25 GB and above
];

export const getColorForSize = (bytes: number): string => {
  return sizeRanges.find((range) => bytes <= range.limit)?.color || "default";
};
