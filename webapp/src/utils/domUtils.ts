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

const CANVAS_CONTEXT = document.createElement("canvas").getContext("2d");
const BODY_FONT = getCssFont();

/**
 * Gets the computed style of the given element.
 *
 * @see https://stackoverflow.com/a/21015393
 *
 * @param element - The element to get the style from.
 * @param prop - The property to get the value of.
 * @returns The computed style of the given element.
 */
export function getCssStyle(element: HTMLElement, prop: string) {
  return window.getComputedStyle(element, null).getPropertyValue(prop);
}

/**
 * Gets the font of the given element, or the `body` element if none is provided.
 * The returned value follows the CSS `font` shorthand property format.
 *
 * @see https://stackoverflow.com/a/21015393
 *
 * @param element - The element to get the font from.
 * @returns The font of the given element.
 */
export function getCssFont(element = document.body) {
  const fontWeight = getCssStyle(element, "font-weight") || "normal";
  const fontSize = getCssStyle(element, "font-size") || "16px";
  const fontFamily = getCssStyle(element, "font-family") || "Arial";

  return `${fontWeight} ${fontSize} ${fontFamily}`;
}

/**
 * Uses `canvas.measureText` to compute and return the width of the specified text,
 * using the specified canvas font if defined (use font from the "body" otherwise).
 *
 * @see https://stackoverflow.com/a/21015393
 *
 * @param text - The text to be rendered.
 * @param [font] - The CSS font that text is to be rendered with (e.g. "bold 14px Arial").
 * If not provided, the font of the `body` element is used.
 * @returns The width of the text in pixels.
 */
export function measureTextWidth(text: string, font?: string) {
  if (CANVAS_CONTEXT) {
    CANVAS_CONTEXT.font = font || BODY_FONT;
    return CANVAS_CONTEXT.measureText(text).width;
  }
  return 0;
}
