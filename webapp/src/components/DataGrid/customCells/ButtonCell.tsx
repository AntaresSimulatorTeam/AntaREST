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

import {
  type CustomCell,
  type CustomRenderer,
  getMiddleCenterBias,
  GridCellKind,
  measureTextCached,
} from "@glideapps/glide-data-grid";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export type ButtonVariant = "contained" | "outlined" | "text";

export interface ButtonCellProps {
  readonly kind: "button-cell";
  /** Text shown inside the button */
  readonly label: string;
  /**
   * Visual style of the button.
   * - "contained" → filled background (primary action)
   * - "outlined"  → border only
   * - "text"      → no border / background (link-like)
   *
   * @default "contained"
   */
  readonly variant?: ButtonVariant;
  /**
   * Optional unicode character or emoji used as a leading icon.
   * e.g. "💾", "✏️", "🗑"
   */
  readonly icon?: string;
  /** When true, the button is greyed-out and unclickable. */
  readonly disabled?: boolean;
  /**
   * Callback fired when the user clicks the button.
   * Receives the cell's own data so the parent can identify which row/action was triggered.
   */
  readonly onClick?: (data: ButtonCellProps) => void;
}

export type ButtonCell = CustomCell<ButtonCellProps>;

////////////////////////////////////////////////////////////////
// Layout constants
////////////////////////////////////////////////////////////////

const BTN_PADDING_H = 10; // horizontal padding inside the button pill
const BTN_PADDING_V = 4; // vertical padding inside the button pill
const BTN_RADIUS = 4; // corner radius
const ICON_GAP = 5; // space between icon and label

////////////////////////////////////////////////////////////////
// Canvas helpers
////////////////////////////////////////////////////////////////

/**
 * Draw a rounded rectangle path (does not fill/stroke).
 *
 * @param ctx
 * @param x
 * @param y
 * @param w
 * @param h
 * @param r
 */
function roundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
): void {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.arcTo(x + w, y, x + w, y + r, r);
  ctx.lineTo(x + w, y + h - r);
  ctx.arcTo(x + w, y + h, x + w - r, y + h, r);
  ctx.lineTo(x + r, y + h);
  ctx.arcTo(x, y + h, x, y + h - r, r);
  ctx.lineTo(x, y + r);
  ctx.arcTo(x, y, x + r, y, r);
  ctx.closePath();
}

/**
 * Clamp a hex/rgba colour to a lower opacity.
 * Used for disabled states.
 *
 * @param color
 * @param alpha
 */
function withAlpha(color: string, alpha: number): string {
  // If it is already rgba, replace the alpha channel
  const rgbaMatch = color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (rgbaMatch) {
    return `rgba(${rgbaMatch[1]},${rgbaMatch[2]},${rgbaMatch[3]},${alpha})`;
  }
  // Hex shorthand: convert to rgba via an offscreen canvas trick is too heavy;
  // just append a CSS alpha override using the `color-mix` trick isn't widely
  // available in canvas. Fall back to appending a hex alpha.
  if (color.startsWith("#")) {
    const hex = color.slice(1);
    const full = hex.length === 3 ? hex.replace(/./g, "$&$&") : hex;
    const alphaHex = Math.round(alpha * 255)
      .toString(16)
      .padStart(2, "0");
    return `#${full}${alphaHex}`;
  }
  return color;
}

////////////////////////////////////////////////////////////////
// Renderer
////////////////////////////////////////////////////////////////

const renderer: CustomRenderer<ButtonCell> = {
  kind: GridCellKind.Custom,

  isMatch: (cell): cell is ButtonCell => (cell.data as ButtonCellProps).kind === "button-cell",

  // ── Canvas drawing ───────────────────────────────────────────
  draw: (args, cell) => {
    const { ctx, theme, rect, highlighted } = args;
    const { label, variant = "contained", icon, disabled = false } = cell.data;

    ctx.save();

    const font = `${theme.baseFontStyle} ${theme.fontFamily}`;
    ctx.font = font;

    const labelWidth = measureTextCached(label, ctx, font).width;
    const iconWidth = icon ? measureTextCached(icon, ctx, font).width + ICON_GAP : 0;
    const contentWidth = labelWidth + iconWidth;

    // Button dimensions — centred inside the cell
    const btnW = Math.min(
      contentWidth + BTN_PADDING_H * 2,
      rect.width - theme.cellHorizontalPadding * 2,
    );
    const btnH = rect.height - BTN_PADDING_V * 2;
    const btnX = rect.x + (rect.width - btnW) / 2;
    const btnY = rect.y + BTN_PADDING_V;
    const yMid = rect.y + rect.height / 2;

    // Resolve colours depending on state
    const effectiveAccent = disabled
      ? withAlpha(theme.accentColor, 0.38)
      : highlighted
        ? theme.accentColor
        : theme.accentColor;

    const effectiveBg = disabled
      ? theme.bgCellMedium
      : highlighted
        ? theme.accentLight
        : theme.bgCell;
    const effectiveText = disabled
      ? theme.textLight
      : variant === "contained"
        ? theme.accentFg
        : effectiveAccent;

    // ── Background / border ───────────────────────────────────
    roundedRect(ctx, btnX, btnY, btnW, btnH, BTN_RADIUS);

    if (variant === "contained") {
      ctx.fillStyle = effectiveAccent;
      ctx.fill();
    } else if (variant === "outlined") {
      ctx.fillStyle = effectiveBg;
      ctx.fill();
      ctx.strokeStyle = effectiveAccent;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    // "text" variant: no background, no border

    // ── Label (and optional icon) ─────────────────────────────
    ctx.fillStyle = effectiveText;
    ctx.textAlign = "center";

    const textBias = getMiddleCenterBias(ctx, font);

    if (icon) {
      // Draw icon + label side-by-side, centred together
      const totalW = iconWidth + labelWidth;
      const startX = btnX + btnW / 2 - totalW / 2;

      ctx.textAlign = "left";
      ctx.fillText(icon, startX, yMid + textBias);
      ctx.fillText(label, startX + iconWidth, yMid + textBias);
    } else {
      ctx.fillText(label, btnX + btnW / 2, yMid + textBias, btnW - BTN_PADDING_H * 2);
    }

    // ── Hover / focus ring (outlined-like glow) ───────────────
    if (highlighted && !disabled && variant === "text") {
      roundedRect(ctx, btnX, btnY, btnW, btnH, BTN_RADIUS);
      ctx.strokeStyle = withAlpha(theme.accentColor, 0.4);
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    ctx.restore();
    return true;
  },

  // ── Click: fire the callback, return undefined so GDG does not open an editor
  onClick: (args) => {
    const cell = args.cell as ButtonCell;
    const { disabled = false, onClick } = cell.data;

    if (!disabled && onClick) {
      onClick(cell.data);
    }

    // Return undefined — we never mutate the cell value directly from a button
    return undefined;
  },

  // ── No overlay editor needed — click is sufficient ───────────
  provideEditor: () => undefined,

  // ── Paste: buttons are not data cells, ignore paste ──────────
  onPaste: (_value, cellData) => cellData,
};

export default renderer;
