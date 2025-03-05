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

import type { GridSelection, Item } from "@glideapps/glide-data-grid";
import { useState } from "react";
import { useUpdateEffect } from "react-use";

interface SelectionStats {
  sum: number;
  average: number;
  min: number;
  max: number;
  count: number;
}

interface UseSelectionStatsProps {
  data: number[][];
  selection: GridSelection;
  gridToData: (coordinates: Item) => Item | null;
}

export function useSelectionStats({ data, selection, gridToData }: UseSelectionStatsProps) {
  const [stats, setStats] = useState<SelectionStats | null>(null);

  useUpdateEffect(() => {
    let sum = 0;
    let min = Number.POSITIVE_INFINITY;
    let max = Number.NEGATIVE_INFINITY;
    let count = 0;
    const numRows = data.length;
    const numCols = data[0]?.length ?? 0;

    const processValue = (value: number) => {
      sum += value;
      min = Math.min(min, value);
      max = Math.max(max, value);
      count++;
    };

    if (selection.current?.range) {
      const { x, y, width, height } = selection.current.range;

      for (let col = x; col < x + width; ++col) {
        for (let row = y; row < y + height; ++row) {
          const coordinates = gridToData([col, row]);

          if (coordinates) {
            const [dataCol, dataRow] = coordinates;
            const value = data[dataRow]?.[dataCol];

            if (value !== undefined) {
              processValue(value);
            }
          }
        }
      }
    }

    for (const row of selection.rows) {
      for (let col = 0; col < numCols; ++col) {
        const value = data[row]?.[col];

        if (value !== undefined) {
          processValue(value);
        }
      }
    }

    for (const col of selection.columns) {
      for (let row = 0; row < numRows; ++row) {
        const coordinates = gridToData([col, row]);

        if (coordinates) {
          const [dataCol, dataRow] = coordinates;
          const value = data[dataRow]?.[dataCol];

          if (value !== undefined) {
            processValue(value);
          }
        }
      }
    }

    setStats(count ? { sum, min, max, count, average: sum / count } : null);
  }, [data, selection]);

  return stats;
}
