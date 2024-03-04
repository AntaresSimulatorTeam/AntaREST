import { useEffect, useState, useRef } from "react";
import debug from "debug";
import HT from "handsontable";
import {
  MatrixIndex,
  MatrixEditDTO,
  MatrixType,
  MatrixStats,
} from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import { Root } from "./style";
import {
  computeStats,
  createDateFromIndex,
  cellChangesToMatrixEdits,
} from "./utils";
import Handsontable, { HotTableClass } from "../Handsontable";

const logError = debug("antares:editablematrix:error");

interface PropTypes {
  matrix: MatrixType;
  matrixIndex?: MatrixIndex;
  matrixTime: boolean;
  readOnly: boolean;
  onUpdate?: (change: MatrixEditDTO[], source: string) => void;
  columnsNames?: string[];
  rowNames?: string[];
  computStats?: MatrixStats;
  isPercentDisplayEnabled?: boolean;
}

type CellType = Array<number | string | boolean>;

const formatColumnName = (col: string) => {
  try {
    const colIndex = parseInt(col, 10);
    if (!Number.isNaN(colIndex)) {
      return `TS-${colIndex + 1}`;
    }
  } catch (e) {
    logError(`Unable to parse matrix column index ${col}`, e);
  }
  return col;
};

function EditableMatrix(props: PropTypes) {
  const {
    readOnly,
    matrix,
    matrixIndex,
    matrixTime,
    onUpdate,
    columnsNames,
    rowNames,
    computStats,
    isPercentDisplayEnabled = false,
  } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0 && matrixTime;
  const [grid, setGrid] = useState<CellType[]>([]);
  const [formattedColumns, setFormattedColumns] = useState<HT.ColumnSettings[]>(
    [],
  );
  const hotTableComponent = useRef<HotTableClass>(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSlice = (changes: HT.CellChange[], source: string) => {
    if (!onUpdate) {
      return;
    }

    const filteredChanges = changes.filter(
      ([, , oldValue, newValue]) =>
        parseFloat(oldValue) !== parseFloat(newValue),
    );

    if (filteredChanges.length > 0) {
      const edits = cellChangesToMatrixEdits(
        filteredChanges,
        matrixTime,
        isPercentDisplayEnabled,
      );

      onUpdate(edits, source);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "a" && e.ctrlKey) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (hotTableComponent.current?.hotInstance) {
        const hot = hotTableComponent.current.hotInstance;
        const cols = computStats === MatrixStats.TOTAL ? 1 : 3;
        hot.selectCell(
          0,
          prependIndex ? 1 : 0,
          hot.countRows() - 1,
          hot.countCols() - (computStats ? cols : 0) - 1,
        );
      }
    }
  };

  useEffect(() => {
    setFormattedColumns([
      ...(prependIndex ? [{ title: "Time", readOnly: true, width: 130 }] : []),
      ...columns.map((col, index) => ({
        title: columnsNames?.[index] || formatColumnName(col),
        readOnly,
      })),
      ...(computStats === MatrixStats.TOTAL
        ? [{ title: "Total", readOnly: true }]
        : []),
      ...(computStats === MatrixStats.STATS
        ? [
            { title: "Min.", readOnly: true },
            { title: "Max.", readOnly: true },
            { title: "Average", readOnly: true },
          ]
        : []),
    ]);

    const tmpData = data.map((row, i) => {
      let tmpRow = row as Array<string | number>;
      if (prependIndex && matrixIndex) {
        tmpRow = [createDateFromIndex(i, matrixIndex)].concat(row);
      }

      if (computStats) {
        tmpRow = tmpRow.concat(
          computeStats(computStats, row) as Array<string | number>,
        );
      }

      if (isPercentDisplayEnabled) {
        tmpRow = tmpRow.map((cell) => {
          if (typeof cell === "number") {
            return cell * 100;
          }
          return cell;
        });
      }

      return tmpRow;
    });

    setGrid(tmpData);
  }, [
    columns,
    columnsNames,
    data,
    index,
    prependIndex,
    readOnly,
    matrixIndex,
    computStats,
    isPercentDisplayEnabled,
  ]);

  const matrixRowNames =
    rowNames || (matrixIndex && index.map((i) => String(i)));

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      <Handsontable
        ref={hotTableComponent}
        data={grid}
        width="100%"
        height="100%"
        className="editableMatrix"
        colHeaders
        rowHeaderWidth={rowNames ? 150 : 50}
        afterChange={(change, source) =>
          onUpdate && handleSlice(change || [], source)
        }
        beforeKeyDown={(e) => handleKeyDown(e)}
        columns={formattedColumns}
        rowHeaders={matrixRowNames || true}
      />
    </Root>
  );
}

export default EditableMatrix;
