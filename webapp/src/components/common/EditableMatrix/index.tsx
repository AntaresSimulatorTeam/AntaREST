import { useEffect, useState, useRef } from "react";
import debug from "debug";
import HotTable from "@handsontable/react";
import { CellChange } from "handsontable/common";
import { ColumnSettings } from "handsontable/settings";
import {
  MatrixIndex,
  MatrixEditDTO,
  MatrixType,
  MatrixStats,
} from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import MatrixGraphView from "./MatrixGraphView";
import { Root } from "./style";
import "./style.css";
import { computeStats, createDateFromIndex, slice } from "./utils";
import Handsontable from "../Handsontable";

const logError = debug("antares:editablematrix:error");

interface PropTypes {
  matrix: MatrixType;
  matrixIndex?: MatrixIndex;
  matrixTime: boolean;
  readOnly: boolean;
  toggleView?: boolean;
  onUpdate?: (change: MatrixEditDTO[], source: string) => void;
  columnsNames?: string[];
  rowNames?: string[];
  computStats?: MatrixStats;
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
    toggleView,
    onUpdate,
    columnsNames,
    rowNames,
    computStats,
  } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0 && matrixTime;
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setFormatedColumns] = useState<ColumnSettings[]>([]);
  const hotTableComponent = useRef<HotTable>(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSlice = (change: CellChange[], source: string) => {
    const isChanged = change.map((item) => {
      if (parseFloat(item[2]) === parseFloat(item[3])) {
        return;
      }
      return item;
    });
    if (onUpdate) {
      const edit = slice(
        isChanged.filter((e) => e !== undefined) as CellChange[]
      );
      onUpdate(edit, source);
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
          hot.countCols() - (computStats ? cols : 0) - 1
        );
      }
    }
  };

  useEffect(() => {
    setFormatedColumns([
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
      let tmpRow = row as (string | number)[];
      if (prependIndex) {
        if (matrixIndex) {
          tmpRow = [createDateFromIndex(i, matrixIndex)].concat(row);
        }
      }
      if (computStats) {
        tmpRow = tmpRow.concat(
          computeStats(computStats, row) as (string | number)[]
        );
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
  ]);

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Root>
      {toggleView ? (
        <Handsontable
          ref={hotTableComponent}
          data={grid}
          width="100%"
          height="100%"
          stretchH="all"
          className="editableMatrix"
          colHeaders
          rowHeaderWidth={rowNames ? 150 : undefined}
          afterChange={(change, source) =>
            onUpdate && handleSlice(change || [], source)
          }
          beforeKeyDown={(e) => handleKeyDown(e)}
          columns={formatedColumns}
          rowHeaders={rowNames || true}
          manualColumnResize
        />
      ) : (
        <MatrixGraphView matrix={matrix} />
      )}
    </Root>
  );
}

export default EditableMatrix;
