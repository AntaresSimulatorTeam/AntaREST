import { useEffect, useState, useRef } from "react";
import _ from "lodash";
import HotTable, { HotColumn } from "@handsontable/react";
import { registerAllModules } from "handsontable/registry";
// eslint-disable-next-line import/no-unresolved
import { CellChange } from "handsontable/common";
import { MatrixIndex, MatrixEditDTO, MatrixType } from "../../../common/types";
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
        hot.selectCell(0, 1, hot.countRows() - 1, hot.countCols() - 1);
      }
    }
  };

  useEffect(() => {
    setFormatedColumns([
      ...(prependIndex ? [{ title: "Time", readOnly: true }] : []),
      ...columns.map((col, index) => ({
        title: columnsNames?.[index] || col,
        readOnly,
      })),
    ]);

    const tmpData = data.map((row, i) => {
      if (prependIndex) {
        if (matrixIndex && !_.isNaN(parseInt(index[0] as string, 10))) {
          return [
            createDateFromIndex(
              i,
              matrixIndex.start_date,
              index,
              matrixIndex.level
            ),
          ].concat(row);
        }
        return [index[i]].concat(row);
      }

      return row;
    });
    setGrid(tmpData);
  }, [columns, columnsNames, data, index, prependIndex, readOnly, matrixIndex]);

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
          colWidths={[220].concat(_.fill(Array(columns.length), 100))}
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
