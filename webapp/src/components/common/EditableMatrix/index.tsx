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
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

function EditableMatrix(props: PropTypes) {
  const { readOnly, matrix, matrixIndex, matrixTime, toggleView, onUpdate } =
    props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0 && matrixTime;
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);
  const hotTableComponent = useRef<HotTable>(null);

  registerAllModules();

  const handleSlice = (change: CellChange[], source: string) => {
    if (onUpdate) {
      const edit = slice(change);
      onUpdate(edit, source);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "a" && e.ctrlKey) {
      e.preventDefault();
      e.stopImmediatePropagation();
      if (hotTableComponent.current) {
        if (hotTableComponent.current.hotInstance) {
          const hot = hotTableComponent.current.hotInstance;
          hot.selectCell(0, 1, hot.countRows() - 1, hot.countCols() - 1);
        }
      }
    }
  };

  const renderView = () => {
    if (toggleView) {
      return (
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
            prependIndex && matrixTime && columns.length <= 10 ? [120] : [220]
          }
        >
          {formatedColumns.map((column) => (
            <HotColumn key={column.title} settings={column} />
          ))}
        </StyledHotTable>
      );
    }
    return <MatrixGraphView matrix={matrix} />;
  };

  useEffect(() => {
    const columnsData: Array<ColumnsType> = (
      prependIndex ? [{ title: "Time", readOnly: true }] : []
    ).concat(columns.map((title) => ({ title: String(title), readOnly })));
    setColumns(columnsData);

    const tmpData = data.map((row, i) => {
      if (prependIndex) {
        if (matrixIndex && !_.isNaN(parseInt(index[0] as string, 10))) {
          return [
            createDateFromIndex(index[i], matrixIndex.start_date, index),
          ].concat(row);
        }
        return [index[i]].concat(row);
      }

      return row;
    });
    setGrid(tmpData);
  }, [columns, data, index, prependIndex, readOnly, matrixIndex]);

  return <Root>{renderView()}</Root>;
}

EditableMatrix.defaultProps = {
  toggleView: true,
  onUpdate: undefined,
  matrixIndex: undefined,
};

export default EditableMatrix;
