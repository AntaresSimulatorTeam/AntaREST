import { useEffect, useState } from "react";
import { Box, ButtonGroup } from "@mui/material";
import TableViewIcon from "@mui/icons-material/TableView";
import BarChartIcon from "@mui/icons-material/BarChart";
import { HotColumn } from "@handsontable/react";
import { MatrixType } from "../../../common/types";
import "handsontable/dist/handsontable.min.css";
import MatrixGraphView from "./MatrixGraphView";
import { Root, StyledButton, StyledHotTable } from "./style";

interface PropTypes {
  matrix: MatrixType;
  readOnly: boolean;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = { title: string; readOnly: boolean };

export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { readOnly, matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const prependIndex = index.length > 0 && typeof index[0] === "string";
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);
  const [toggleView, setToggleView] = useState<boolean>(true);

  const renderView = () => {
    if (toggleView) {
      return (
        <StyledHotTable
          data={grid}
          licenseKey="non-commercial-and-evaluation"
          width="100%"
          height="100%"
          stretchH="all"
        >
          {formatedColumns.map((column) => (
            <HotColumn key={column.title} settings={column} />
          ))}
        </StyledHotTable>
      );
    }
    return <MatrixGraphView matrix={matrix} />;
  };

  const changeView = () => setToggleView(!toggleView);

  useEffect(() => {
    const columnsData: Array<ColumnsType> = (
      prependIndex ? [{ title: "Time", readOnly }] : []
    ).concat(
      columns.map((title) => ({ title: String(title), readOnly: false }))
    );
    setColumns(columnsData);

    const tmpData = data.map((row, i) =>
      prependIndex ? [index[i]].concat(row) : row
    );
    setGrid(tmpData);
  }, [columns, data, index, prependIndex, readOnly]);

  return (
    <Root>
      <Box width="100%" display="flex" justifyContent="center">
        <ButtonGroup sx={{ mb: 3 }} variant="contained">
          <StyledButton
            onClick={toggleView ? undefined : changeView}
            disabled={toggleView}
          >
            <TableViewIcon sx={{ color: "text.main" }} />
          </StyledButton>
          <StyledButton
            onClick={toggleView ? changeView : undefined}
            disabled={!toggleView}
          >
            <BarChartIcon sx={{ color: "text.main" }} />
          </StyledButton>
        </ButtonGroup>
      </Box>
      {renderView()}
    </Root>
  );
}
