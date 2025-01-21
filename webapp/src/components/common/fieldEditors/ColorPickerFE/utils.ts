/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import type { ColorResult } from "react-color";

export function stringToRGB(color: string): ColorResult["rgb"] | undefined {
  let sColor;
  try {
    sColor = color.split(",").map((elm) => parseInt(elm.replace(/\s+/g, ""), 10));
  } catch {
    sColor = undefined;
  }

  if (sColor && sColor.length === 3) {
    return {
      r: sColor[0],
      g: sColor[1],
      b: sColor[2],
    };
  }
  return undefined;
}

export function rgbToString(color: Partial<ColorResult["rgb"]>): string {
  const { r, g, b } = color;
  if (r === undefined || g === undefined || b === undefined) {
    return "";
  }
  return `${r},${g},${b}`;
}
