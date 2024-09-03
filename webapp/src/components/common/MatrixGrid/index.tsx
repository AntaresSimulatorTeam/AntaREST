import "@glideapps/glide-data-grid/dist/index.css";
import DataEditor, {
  CompactSelection,
  EditListItem,
  EditableGridCell,
  GridSelection,
  Item,
} from "@glideapps/glide-data-grid";
import { useGridCellContent } from "./useGridCellContent";
import { useRef, useState } from "react";
import { type CellFillPattern, type EnhancedGridColumn } from "./types";
import { darkTheme } from "./utils";
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
  onCellEdit?: (cell: Item, newValue: number) => void;
  onMultipleCellsEdit?: (
    updates: Array<{ coordinates: Item; value: number }>,
    fillPattern?: CellFillPattern,
  ) => void;
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
}: MatrixGridProps) {
  const [selection, setSelection] = useState<GridSelection>({
    columns: CompactSelection.empty(),
    rows: CompactSelection.empty(),
  });

  const fillPatternRef = useRef<CellFillPattern | null>(null);

  const { gridToData } = useColumnMapping(columns);

  const getCellContent = useGridCellContent(
    data,
    columns,
    gridToData,
    dateTime,
    aggregates,
    rowHeaders,
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleCellEdited = (cell: Item, value: EditableGridCell) => {
    const updatedValue = value.data;

    if (typeof updatedValue !== "number" || isNaN(updatedValue)) {
      // Invalid numeric value
      return;
    }

    const dataCell = gridToData(cell);

    if (dataCell && onCellEdit) {
      onCellEdit(dataCell, updatedValue);
    }
  };

  const handleCellsEdited = (newValues: readonly EditListItem[]) => {
    const updates = newValues
      .map((edit) => {
        const dataCell = gridToData(edit.location);
        return dataCell
          ? {
              coordinates: dataCell,
              value: edit.value.data as number,
            }
          : null;
      })
      .filter(
        (update): update is { coordinates: Item; value: number } =>
          update !== null,
      );

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
      onMultipleCellsEdit(updates, fillPatternRef.current || undefined);
    }

    // Reset fillPatternRef after use
    fillPatternRef.current = null;

    // Return true to prevent calling `onCellEdit`
    // for each cell after`onMultipleCellsEdit` is called
    return true;
  };

  // Used for fill handle updates to send one batch update object
  // instead of an array of updates using `onCellsEdited` callback
  const handleFillPattern = ({
    patternSource,
    fillDestination,
  }: CellFillPattern) => {
    fillPatternRef.current = { patternSource, fillDestination };
    // Don't prevent default, allow the grid to apply the fill pattern
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <DataEditor
        theme={darkTheme}
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
        onFillPattern={handleFillPattern}
        rowMarkers="both"
      />
      <div id="portal" />
    </>
  );
}

export default MatrixGrid;
