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
import { MenuItem, Select, type SelectChangeEvent } from "@mui/material";

////////////////////////////////////////////////////////////////
// Types
////////////////////////////////////////////////////////////////

export interface SelectCellProps {
  readonly kind: "select-cell";
  /** Currently selected value. */
  readonly value: string;
  /** List of available options. */
  readonly options: ReadonlyArray<string | { value: string; label: string }>;
  /** When true the cell cannot be edited. */
  readonly readonly?: boolean;
}

export type SelectCell = CustomCell<SelectCellProps>;

////////////////////////////////////////////////////////////////
// Helpers
////////////////////////////////////////////////////////////////

function toOption(opt: SelectCellProps["options"][number]): { value: string; label: string } {
  return typeof opt === "string" ? { value: opt, label: opt } : opt;
}

function getLabelForValue(value: string, options: SelectCellProps["options"]): string {
  for (const opt of options) {
    const { value: v, label: l } = toOption(opt);
    if (v === value) {
      return l;
    }
  }
  return value;
}

////////////////////////////////////////////////////////////////
// Canvas chevron icon
////////////////////////////////////////////////////////////////

const ICON_SIZE = 10;
const ICON_PADDING = 6;

/* eslint-disable no-param-reassign */
function drawChevron(ctx: CanvasRenderingContext2D, x: number, y: number, color: string): void {
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.moveTo(x, y + ICON_SIZE * 0.3);
  ctx.lineTo(x + ICON_SIZE / 2, y + ICON_SIZE * 0.7);
  ctx.lineTo(x + ICON_SIZE, y + ICON_SIZE * 0.3);
  ctx.stroke();
  ctx.restore();
}
/* eslint-enable no-param-reassign */

////////////////////////////////////////////////////////////////
// Renderer
////////////////////////////////////////////////////////////////

const renderer: CustomRenderer<SelectCell> = {
  kind: GridCellKind.Custom,

  isMatch: (cell): cell is SelectCell => (cell.data as SelectCellProps).kind === "select-cell",

  // ── Canvas drawing ──────────────────────────────────────────
  draw: (args, cell) => {
    const { ctx, theme, rect, highlighted } = args;
    const { value, options, readonly } = cell.data;

    const label = getLabelForValue(value, options);
    const font = `${theme.baseFontStyle} ${theme.fontFamily}`;
    const paddingH = theme.cellHorizontalPadding;
    const iconAreaWidth = ICON_SIZE + ICON_PADDING * 2;
    const textMaxWidth = rect.width - paddingH * 2 - iconAreaWidth;
    const yMid = rect.y + rect.height / 2;

    ctx.save();

    if (label) {
      ctx.font = font;
      const textWidth = Math.min(measureTextCached(label, ctx, font).width, textMaxWidth);
      const pillW = textWidth + paddingH * 2;
      const pillH = rect.height * 0.62;
      const pillX = rect.x + paddingH;
      const pillY = yMid - pillH / 2;
      const pillRadius = pillH / 2;

      ctx.beginPath();
      ctx.roundRect(pillX, pillY, pillW, pillH, pillRadius);
      ctx.fillStyle = highlighted
        ? theme.accentLight
        : readonly
          ? theme.bgCellMedium
          : theme.bgBubble;
      ctx.fill();

      ctx.fillStyle = theme.textDark;
      ctx.textAlign = "left";
      ctx.fillText(label, pillX + paddingH, yMid + getMiddleCenterBias(ctx, font), textMaxWidth);
    }

    if (!readonly) {
      const iconX = rect.x + rect.width - ICON_SIZE - ICON_PADDING;
      const iconY = yMid - ICON_SIZE / 2;
      drawChevron(ctx, iconX, iconY, theme.textLight);
    }

    ctx.restore();

    return true;
  },

  // ── React editor overlay ─────────────────────────────────────
  provideEditor: () => (props) => {
    const { value: cell, onChange, onFinishedEditing } = props;
    const { value, options, readonly } = cell.data;

    if (readonly) {
      return null;
    }

    const handleChange = (e: SelectChangeEvent<string>) => {
      const next = { ...cell, data: { ...cell.data, value: e.target.value } };
      onChange(next);
      onFinishedEditing(next);
    };

    return (
      <Select
        autoFocus
        open
        value={value}
        onChange={handleChange}
        onClose={() => onFinishedEditing(undefined)}
        variant="outlined"
        size="small"
        sx={{
          width: "100%",
          height: "100%",
          "& .MuiOutlinedInput-notchedOutline": { border: "none" },
          "& .MuiSelect-select": {
            py: 0,
            display: "flex",
            alignItems: "center",
            height: "100%",
          },
        }}
      >
        {options.map((opt) => {
          const { value: v, label: l } = toOption(opt);
          return (
            <MenuItem key={v} value={v} dense>
              {l}
            </MenuItem>
          );
        })}
      </Select>
    );
  },

  // ── Paste handling ────────────────────────────────────────────
  onPaste: (pastedValue, cellData) => {
    const normalised = pastedValue.trim();
    const match = cellData.options.find((opt) => {
      const { value, label } = toOption(opt);
      return value === normalised || label === normalised;
    });
    if (!match) {
      return cellData;
    }
    return { ...cellData, value: toOption(match).value };
  },
};

export default renderer;
