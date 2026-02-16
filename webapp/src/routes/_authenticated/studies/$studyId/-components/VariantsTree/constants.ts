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

export const COLORS = ["#24CF9D", "#F3C918", "#E317DA", "#00B2FF"] as const;

/** Horizontal space allocated per depth level. */
export const TILE_SIZE_X = 50;
/** Vertical space allocated per tree row. */
export const TILE_SIZE_Y = 50;
export const TILE_SIZE_X_2 = TILE_SIZE_X / 2;
export const TILE_SIZE_Y_2 = TILE_SIZE_Y / 2;
export const CIRCLE_RADIUS = 12;
/** Circle center X offset within a tile. */
export const DCX = TILE_SIZE_X_2;
/** Circle center Y offset within a tile. */
export const DCY = TILE_SIZE_Y - CIRCLE_RADIUS;
export const STROKE_WIDTH = 3;
/** Horizontal gap before the curve connects to a child circle. */
export const CURVE_OFFSET = 4;
/** Horizontal gap between the tree-lines area and the text label area. */
export const RECT_X_SPACING = 8;
/** Vertical gap subtracted from tile height to produce the rect height. */
export const RECT_Y_SPACING = 8;
export const RECT_Y_SPACING_2 = RECT_Y_SPACING / 2;
/** Width of the thin colour accent bar on the left edge of the label rect. */
export const RECT_DECORATION = 3;
/** Gap between the accent bar and the text. */
export const TEXT_SPACING = 10;
export const TEXT_SIZE = 20;
/** Default width reserved for the text label column. */
export const RECT_TEXT_WIDTH = 350;
/**
 * Factor applied to the viewBox to control the tree's zoom level.
 * Higher values zoom out (showing more of the tree), lower values zoom in.
 * Adjust this value to make tree nodes appear larger or smaller.
 */
export const ZOOM_OUT = 1.5;
/** Minimum width for the tree-lines area (0 = no minimum). */
export const MIN_WIDTH = 0;
/** Extra depth levels added when computing the tree-lines area width. */
export const DEPTH_OFFSET = 0;
