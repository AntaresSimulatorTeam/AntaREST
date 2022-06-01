import { useEffect, useState, useRef } from "react";
import HotTable, { HotColumn } from "@handsontable/react";
import { registerAllModules } from "handsontable/registry";
import moment from "moment";
import { MatrixIndex, MatrixType } from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import MatrixGraphView from "./MatrixGraphView";
import { Root, StyledHotTable } from "./style";
import "./style.css";
import {
  CellChange,
  MatrixEditDTO,
} from "../../singlestudy/explore/Modelization/Matrix/type";
import { slice } from "../../singlestudy/explore/Modelization/Matrix/utils";

interface PropTypes {
  matrix: MatrixType;
  matrixIndex?: MatrixIndex;
  readOnly: boolean;
  toggleView?: boolean;
  onUpdate?: (change: MatrixEditDTO[], source: string) => void;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

function EditableMatrix(props: PropTypes) {
  const { readOnly, matrix, matrixIndex, toggleView, onUpdate } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0;
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
      // CTRL + A
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
        >
          {formatedColumns.map((column) => (
            <HotColumn key={column.title} settings={column} />
          ))}
        </StyledHotTable>
      );
    }
    return <MatrixGraphView matrix={matrix} />;
  };

  const createDateFromIndex = (
    truc: string | number,
    startDate: string
  ): string | number => {
    const date = moment
      .utc(startDate)
      .add(truc, "h")
      .format("(ww) - ddd DD MMM HH:mm");
    return `${truc.toString().padStart(4, "0")} ${date}`;
  };

  useEffect(() => {
    const columnsData: Array<ColumnsType> = (
      prependIndex && matrixIndex ? [{ title: "Time", readOnly: true }] : []
    ).concat(columns.map((title) => ({ title: String(title), readOnly })));
    setColumns(columnsData);

    const tmpData = data.map((row, i) => {
      if (prependIndex) {
        if (matrixIndex) {
          return [createDateFromIndex(index[i], matrixIndex.start_date)].concat(
            row
          );
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
