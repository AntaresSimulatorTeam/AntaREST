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

import { useMemo } from "react";
import type { AggregateType, EnhancedGridColumn } from "../shared/types";
import { Column, Aggregate } from "../shared/constants";
import { generateDataColumns } from "../shared/utils";
import { aggregatesAvgTheme, aggregatesTheme, dateTimeTheme } from "../styles";
import useThemeColorScheme from "@/hooks/useThemeColorScheme";

interface UseMatrixColumnsProps {
  data: number[][];
  dateTimeColumn: boolean;
  enableRowHeaders: boolean;
  isTimeSeries: boolean;
  customColumns?: string[] | readonly string[];
  colWidth?: number;
  aggregateTypes: AggregateType[];
}

export function useMatrixColumns({
  data,
  dateTimeColumn,
  enableRowHeaders,
  isTimeSeries,
  customColumns,
  colWidth,
  aggregateTypes,
}: UseMatrixColumnsProps) {
  const { isDarkMode } = useThemeColorScheme();

  // Use scalar counts instead of the data reference so pasting (which changes
  // data values but not shape) does not invalidate the memo and produce a new
  // columns array reference. A new reference would trigger DataGrid's
  // useUpdateEffect reset, undoing any column-width adjustments made after paste.
  const rowCount = data.length;
  const columnCount = data[0]?.length ?? 0;

  return useMemo(() => {
    if (rowCount === 0 || columnCount === 0) {
      return [];
    }

    const baseColumns: EnhancedGridColumn[] = [];

    if (dateTimeColumn) {
      baseColumns.push({
        id: "date",
        title: "Date",
        type: Column.DateTime,
        editable: false,
        themeOverride: isDarkMode ? dateTimeTheme.dark : dateTimeTheme.light,
      });
    }

    if (enableRowHeaders) {
      baseColumns.unshift({
        id: "rowHeaders",
        title: "",
        type: Column.Text,
        editable: false,
      });
    }

    const dataColumns = generateDataColumns({
      isTimeSeries,
      count: columnCount,
      customColumns,
      width: colWidth,
    });

    const aggregatesColumns: EnhancedGridColumn[] = aggregateTypes.map((aggregateType) => ({
      id: aggregateType,
      title: aggregateType.charAt(0).toUpperCase() + aggregateType.slice(1),
      type: Column.Aggregate,
      editable: false,
      themeOverride:
        aggregateType === Aggregate.Avg
          ? isDarkMode
            ? aggregatesAvgTheme.dark
            : aggregatesAvgTheme.light
          : isDarkMode
            ? aggregatesTheme.dark
            : aggregatesTheme.light,
    }));

    return [...baseColumns, ...dataColumns, ...aggregatesColumns];
  }, [
    rowCount,
    columnCount,
    dateTimeColumn,
    enableRowHeaders,
    isTimeSeries,
    customColumns,
    colWidth,
    aggregateTypes,
    isDarkMode,
  ]);
}
