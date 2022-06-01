import { useEffect, useState } from "react";
import { HotColumn } from "@handsontable/react";
import { registerAllModules } from "handsontable/registry";
import { MatrixType } from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import MatrixGraphView from "./MatrixGraphView";
import { Root, StyledHotTable } from "./style";
import "./style.css";
import { CellChange } from "../../singlestudy/explore/Modelization/Matrix/type";

interface PropTypes {
  matrix: MatrixType;
  readOnly: boolean;
  toggleView?: boolean;
  onUpdate?: (change: CellChange[], source: string) => void;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

function EditableMatrix(props: PropTypes) {
  const { readOnly, matrix, toggleView, onUpdate } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0;
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);

  registerAllModules();

  const renderView = () => {
    if (toggleView) {
      return (
        <StyledHotTable
          data={grid}
          licenseKey="non-commercial-and-evaluation"
          width="100%"
          height="100%"
          stretchH="all"
          className="editableMatrix"
          colHeaders
          afterChange={(change, source) =>
            onUpdate && onUpdate(change || [], source)
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
      prependIndex ? [{ title: "Time", readOnly }] : []
    ).concat(columns.map((title) => ({ title: String(title), readOnly })));
    setColumns(columnsData);

    const tmpData = data.map((row, i) =>
      prependIndex ? [index[i]].concat(row) : row
    );
    setGrid(tmpData);
  }, [columns, data, index, prependIndex, readOnly]);

  return <Root>{renderView()}</Root>;
}

EditableMatrix.defaultProps = {
  toggleView: true,
  onUpdate: undefined,
};

export default EditableMatrix;
