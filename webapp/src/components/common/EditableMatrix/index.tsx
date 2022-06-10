import { useEffect, useState, useRef } from "react";
import _ from "lodash";
import HotTable, { HotColumn } from "@handsontable/react";
import { registerAllModules } from "handsontable/registry";
// eslint-disable-next-line import/no-unresolved
import { CellChange } from "handsontable/common";
import {
  MatrixIndex,
  MatrixEditDTO,
  MatrixType,
  MatrixStats,
} from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import MatrixGraphView from "./MatrixGraphView";
import { Root, StyledHotTable } from "./style";
import "./style.css";
import { createDateFromIndex, slice } from "./utils";

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

// TODO https://handsontable.com/docs/react-modules/#step-1-import-the-handsontable-base-module
registerAllModules();

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
  // Utils
  ////////////////////////////////////////////////////////////////

  const addStats = (computStats: string, row: Array<number>) => {
    if (computStats === MatrixStats.TOTAL) {
      return row.reduce((agg, value) => {
        return agg + value;
      }, 0);
    }
    if (computStats === MatrixStats.STATS) {
      const statsInfo = row.reduce(
        (agg, value) => {
          const newAgg = { ...agg };
          if (value < agg.min) {
            newAgg.min = value;
          }
          if (value > agg.max) {
            newAgg.max = value;
          }
          newAgg.total = agg.total + value;

          return newAgg;
        },
        { min: row[0], max: row[0], total: 0 }
      );
      return [statsInfo.min, statsInfo.max, statsInfo.total / row.length];
    }
  };

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
        const cols = computStats === MatrixStats.TOTAL ? 2 : 4;
        hot.selectCell(
          0,
          1,
          hot.countRows() - 1,
          hot.countCols() - (computStats ? cols : 1)
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
          addStats(computStats, row) as (string | number)[]
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
        <StyledHotTable
          ref={hotTableComponent}
          data={grid}
          licenseKey="non-commercial-and-evaluation"
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
          manualColumnResize
        >
          {formatedColumns.map((column) => (
            <HotColumn key={column.title} settings={column} />
          ))}
        </StyledHotTable>
      ) : (
        <MatrixGraphView matrix={matrix} />
      )}
    </Root>
  );
}

export default EditableMatrix;
