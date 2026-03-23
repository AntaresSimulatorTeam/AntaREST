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
} from "@glideapps/glide-data-grid";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface ToggleCellProps {
  readonly kind: "toggle-cell";
  /** Current on/off state. */
  readonly value: boolean;
  /** Optional label shown to the right of the switch. */
  readonly label?: string;
  /** When true the cell cannot be toggled. */
  readonly readonly?: boolean;
}

export type ToggleCell = CustomCell<ToggleCellProps>;

////////////////////////////////////////////////////////////////
// Layout constants
////////////////////////////////////////////////////////////////

const TRACK_W = 32;
const TRACK_H = 16;
const THUMB_R = 6;
const THUMB_MARGIN = 2;

////////////////////////////////////////////////////////////////
// Canvas helpers
////////////////////////////////////////////////////////////////

/* eslint-disable no-param-reassign */

function pillRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number): void {
  const r = h / 2;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function drawToggle(
  ctx: CanvasRenderingContext2D,
  trackX: number,
  trackY: number,
  value: boolean,
  readonly: boolean,
  accentColor: string,
  bgBubble: string,
  bgCellMedium: string,
): void {
  ctx.save();

  // ── Track ──────────────────────────────────────────────────
  const trackColor = value ? (readonly ? `${accentColor}88` : accentColor) : bgBubble;

  pillRect(ctx, trackX, trackY, TRACK_W, TRACK_H);
  ctx.fillStyle = trackColor;
  ctx.fill();

  pillRect(ctx, trackX, trackY, TRACK_W, TRACK_H);
  ctx.strokeStyle = value ? "transparent" : bgCellMedium;
  ctx.lineWidth = 1;
  ctx.stroke();

  // ── Thumb ──────────────────────────────────────────────────
  const thumbCenterY = trackY + TRACK_H / 2;
  const thumbCenterX = value
    ? trackX + TRACK_W - THUMB_MARGIN - THUMB_R
    : trackX + THUMB_MARGIN + THUMB_R;

  ctx.beginPath();
  ctx.arc(thumbCenterX, thumbCenterY, THUMB_R, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.shadowColor = "rgba(0,0,0,0.25)";
  ctx.shadowBlur = 3;
  ctx.fill();
  ctx.shadowBlur = 0;

  ctx.restore();
}

/* eslint-enable no-param-reassign */

////////////////////////////////////////////////////////////////
// Renderer
////////////////////////////////////////////////////////////////

const renderer: CustomRenderer<ToggleCell> = {
  kind: GridCellKind.Custom,

  isMatch: (cell): cell is ToggleCell => (cell.data as ToggleCellProps).kind === "toggle-cell",

  // ── Canvas drawing ─────────────────────────────────────────
  draw: (args, cell) => {
    const { ctx, theme, rect } = args;
    const { value, label, readonly = false } = cell.data;

    const yMid = rect.y + rect.height / 2;
    const paddingH = theme.cellHorizontalPadding;

    const trackX = rect.x + paddingH;
    const trackY = yMid - TRACK_H / 2;

    drawToggle(
      ctx,
      trackX,
      trackY,
      value,
      readonly,
      theme.accentColor,
      theme.bgBubble,
      theme.bgCellMedium,
    );

    if (label !== undefined) {
      const font = `${theme.baseFontStyle} ${theme.fontFamily}`;
      ctx.save();

      ctx.font = font;

      ctx.fillStyle = readonly ? theme.textLight : theme.textDark;

      ctx.textAlign = "left";
      ctx.fillText(label, trackX + TRACK_W + paddingH, yMid + getMiddleCenterBias(ctx, font));
      ctx.restore();
    }

    return true;
  },

  // ── Click: toggle directly without opening an overlay ──────
  onClick: (args) => {
    const cell = args.cell as ToggleCell;

    if (cell.data.readonly) {
      return undefined;
    }

    return {
      ...cell,
      data: {
        ...cell.data,
        value: !cell.data.value,
      },
    };
  },

  // ── No overlay editor needed — click handles everything ────
  provideEditor: () => undefined,

  // ── Paste: accept common truthy/falsy strings ───────────────
  onPaste: (pastedValue, cellData) => {
    const normalised = pastedValue.trim().toLowerCase();

    const truthySet = new Set(["true", "1", "yes", "on", "enabled"]);
    const falsySet = new Set(["false", "0", "no", "off", "disabled"]);

    if (truthySet.has(normalised)) {
      return { ...cellData, value: true };
    }

    if (falsySet.has(normalised)) {
      return { ...cellData, value: false };
    }

    return cellData;
  },
};

export default renderer;
