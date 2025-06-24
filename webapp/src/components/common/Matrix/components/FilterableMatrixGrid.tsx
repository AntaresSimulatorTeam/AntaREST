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

import { Box } from "@mui/material";
import { useState, useEffect, useMemo } from "react";
import { MatrixProvider } from "../context/MatrixContext";
import MatrixGrid, { type MatrixGridProps } from "./MatrixGrid";
import MatrixFilter from "./MatrixFilter";
import type { FilterCriteria } from "./MatrixFilter/types";
import type { TimeFrequencyType } from "../shared/types";

export interface FilterableMatrixGridProps extends MatrixGridProps {
  timeFrequency?: TimeFrequencyType;
}

function FilterableMatrixGrid({
  data,
  rows,
  columns,
  dateTime,
  aggregates,
  rowHeaders,
  onCellEdit,
  onMultipleCellsEdit,
  readOnly = true,
  showPercent,
  showStats = true,
  timeFrequency,
}: FilterableMatrixGridProps) {
  // Initialize filter preview state
  const [filterPreview, setFilterPreview] = useState<{
    active: boolean;
    criteria: FilterCriteria;
  }>(() => ({
    active: false,
    criteria: {
      columnsIndices: Array.from({ length: data[0]?.length || 0 }, (_, i) => i),
      rowsIndices: Array.from({ length: rows }, (_, i) => i),
    },
  }));

  // Update filter criteria when data dimensions change
  useEffect(() => {
    if (!filterPreview.active && data.length > 0) {
      setFilterPreview((prev) => ({
        ...prev,
        criteria: {
          columnsIndices: Array.from({ length: data[0]?.length || 0 }, (_, i) => i),
          rowsIndices: Array.from({ length: rows }, (_, i) => i),
        },
      }));
    }
  }, [data, rows, filterPreview.active]);

  // Create minimal context value for MatrixProvider
  // Only includes what's necessary for filtering functionality
  const contextValue = useMemo(
    () => ({
      // State required by MatrixProvider
      currentState: { data, aggregates: aggregates || {} },
      isSubmitting: false,
      updateCount: 0,
      aggregateTypes: [],

      // Stub implementations for functions we don't use
      setMatrixData: () => {
        // No-op: We don't modify data in this component
      },
      undo: () => {
        // No-op: No undo functionality needed
      },
      redo: () => {
        // No-op: No redo functionality needed
      },
      canUndo: false,
      canRedo: false,
      isDirty: false,
    }),
    [data, aggregates],
  );

  // Determine if this is a time series based on dateTime presence
  const isTimeSeries = !!dateTime && dateTime.length > 0;

  return (
    <MatrixProvider {...contextValue}>
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: 1,
          height: 1,
          position: "relative",
        }}
      >
        {/* TODO: The MatrixFilter button is absolutely positioned because this component
            is used in the results view where the parent controls the layout, preventing
            us from properly placing the filter button in the natural flow.

            This is not ideal and we should find a better solution:
            - Option 1: Accept an optional prop to render the filter in a designated slot/area
            - Option 2: Use a render prop pattern to let the parent decide where to place the filter
            - Option 3: Create a separate non-filterable MatrixGrid and compose them differently
            - Option 4: Refactor the results view to provide better layout control

            The current solution is fragile and breaks if the parent layout changes. */}
        <Box
          sx={{
            position: "absolute",
            top: -50,
            right: 150,
            zIndex: 1,
          }}
        >
          <MatrixFilter
            dateTime={dateTime}
            isTimeSeries={isTimeSeries}
            timeFrequency={timeFrequency}
            readOnly={readOnly}
          />
        </Box>

        <Box sx={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>
          <MatrixGrid
            data={data}
            rows={rows}
            columns={columns}
            dateTime={dateTime}
            aggregates={aggregates}
            rowHeaders={rowHeaders}
            width="100%"
            height="100%"
            onCellEdit={onCellEdit}
            onMultipleCellsEdit={onMultipleCellsEdit}
            readOnly={readOnly}
            showPercent={showPercent}
            showStats={showStats}
          />
        </Box>
      </Box>
    </MatrixProvider>
  );
}

export default FilterableMatrixGrid;
