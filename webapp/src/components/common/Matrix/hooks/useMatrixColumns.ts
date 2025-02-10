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

import { useMemo } from "react";
import type { AggregateType, EnhancedGridColumn } from "../shared/types";
import { Column, Aggregate } from "../shared/constants";
import { generateDataColumns } from "../shared/utils";
import { aggregatesTheme } from "../styles";

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
  return useMemo(() => {
    if (!data || data.length === 0) {
      return [];
    }

    const columnCount = data[0].length;

    const baseColumns: EnhancedGridColumn[] = [];

    if (dateTimeColumn) {
      baseColumns.push({
        id: "date",
        title: "Date",
        type: Column.DateTime,
        editable: false,
        themeOverride: { bgCell: "#2D2E40" },
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
          ? aggregatesTheme
          : { ...aggregatesTheme, bgCell: "#464770" },
    }));

    return [...baseColumns, ...dataColumns, ...aggregatesColumns];
  }, [
    data,
    dateTimeColumn,
    enableRowHeaders,
    isTimeSeries,
    customColumns,
    colWidth,
    aggregateTypes,
  ]);
}
