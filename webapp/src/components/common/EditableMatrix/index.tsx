import { useEffect, useState, useRef } from "react";
import _ from "lodash";
import HotTable from "@handsontable/react";
import { CellChange } from "handsontable/common";
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

interface PropTypes {
  matrix: MatrixType;
  matrixIndex?: MatrixIndex;
  matrixTime: boolean;
  readOnly: boolean;
  toggleView?: boolean;
  onUpdate?: (change: MatrixEditDTO[], source: string) => void;
  columnsNames?: string[];
  computStats?: MatrixStats;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

function EditableMatrix(props: PropTypes) {
  const {
    readOnly,
    matrix,
    matrixIndex,
    matrixTime,
    toggleView,
    onUpdate,
    columnsNames,
    computStats,
  } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0 && matrixTime;
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setFormatedColumns] = useState<Array<ColumnsType>>(
    []
  );
  const hotTableComponent = useRef<HotTable>(null);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSlice = (change: CellChange[], source: string) => {
    const isChanged = change.map((item) => {
      if (parseInt(item[2], 10) === parseInt(item[3], 10)) {
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
      ...(prependIndex ? [{ title: "Time", readOnly: true }] : []),
      ...columns.map((col, index) => ({
        title: columnsNames?.[index] || String(col),
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
          tmpRow = [
            createDateFromIndex(i, matrixIndex.start_date, matrixIndex.level),
          ].concat(row);
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
          afterChange={(change, source) =>
            onUpdate && handleSlice(change || [], source)
          }
          beforeKeyDown={(e) => handleKeyDown(e)}
          colWidths={
            prependIndex
              ? [220].concat(_.fill(Array(formatedColumns.length), 100))
              : _.fill(Array(formatedColumns.length), 100)
          }
          columns={formatedColumns}
          manualColumnResize
        />
      ) : (
        <MatrixGraphView matrix={matrix} />
      )}
    </Root>
  );
}

export default EditableMatrix;
