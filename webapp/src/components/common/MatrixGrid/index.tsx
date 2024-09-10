import "@glideapps/glide-data-grid/dist/index.css";
import DataEditor, {
  CompactSelection,
  EditableGridCell,
  EditListItem,
  GridCellKind,
  GridSelection,
  Item,
} from "@glideapps/glide-data-grid";
import { useGridCellContent } from "./useGridCellContent";
import { useMemo, useState } from "react";
import { EnhancedGridColumn, GridUpdate } from "./types";
import { darkTheme, readOnlyDarkTheme } from "./utils";
import { useColumnMapping } from "./useColumnMapping";

export interface MatrixGridProps {
  data: number[][];
  rows: number;
  columns: EnhancedGridColumn[];
  dateTime?: string[];
  aggregates?: Record<string, number[]>;
  rowHeaders?: string[];
  width?: string;
  height?: string;
  onCellEdit?: (update: GridUpdate) => void;
  onMultipleCellsEdit?: (updates: GridUpdate[]) => void;
  readOnly?: boolean;
}

function MatrixGrid({
  data,
  rows,
  columns,
  dateTime,
  aggregates,
  rowHeaders,
  width = "100%",
  height = "100%",
  onCellEdit,
  onMultipleCellsEdit,
  readOnly = false,
}: MatrixGridProps) {
  const [selection, setSelection] = useState<GridSelection>({
    columns: CompactSelection.empty(),
    rows: CompactSelection.empty(),
  });

  const { gridToData } = useColumnMapping(columns);

  const theme = useMemo(() => {
    if (readOnly) {
      return {
        ...darkTheme,
        ...readOnlyDarkTheme,
      };
    }

    return darkTheme;
  }, [readOnly]);

  const getCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
    readOnly,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellEdited = (coordinates: Item, value: EditableGridCell) => {
    if (value.kind !== GridCellKind.Number) {
      // Invalid numeric value
      return;
    }

    const dataCoordinates = gridToData(coordinates);

    if (dataCoordinates && onCellEdit) {
      onCellEdit({ coordinates: dataCoordinates, value });
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit): GridUpdate | null => {
        const dataCoordinates = gridToData(edit.location);

        if (edit.value.kind !== GridCellKind.Number || !dataCoordinates) {
          return null;
        }

        return {
          coordinates: dataCoordinates,
          value: edit.value,
        };
      })
      .filter((update): update is GridUpdate => update !== null);

    if (updates.length === 0) {
      // No valid updates
      return;
    }

    if (onCellEdit && updates.length === 1) {
      // If only one cell is edited,`onCellEdit` is called
      // we don't need to call `onMultipleCellsEdit`
      return;
    }

    if (onMultipleCellsEdit) {
      onMultipleCellsEdit(updates);
    }

    // Return true to prevent calling `onCellEdit`
    // for each cell after`onMultipleCellsEdit` is called
    return true;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <DataEditor
        theme={theme}
        width={width}
        height={height}
        rows={rows}
        columns={columns}
        getCellContent={getCellContent}
        onCellEdited={handleCellEdited}
        onCellsEdited={handleCellsEdited}
        gridSelection={selection}
        onGridSelectionChange={setSelection}
        getCellsForSelection // Enable copy support
        onPaste
        fillHandle
        rowMarkers="both"
      />
      <div id="portal" />
    </>
  );
}

export default MatrixGrid;