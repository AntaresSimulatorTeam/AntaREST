import React, { useEffect, useState } from 'react';
import ReactDataSheet from 'react-datasheet';
import 'react-datasheet/lib/react-datasheet.css';
// import "./styles.css";
// import jspreadsheet from 'jspreadsheet-ce';
import { MatrixType } from '../../../../common/types';
import theme from '../../../../App/theme';
// import './jexcel.css';
// import './jsuites.css';

interface PropTypes {
  data: MatrixType;
}

type CellType = Array<{value: number | string; readOnly: boolean | undefined}>

/* export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { data = [], columns = [], index = [] } = props.data;
  const jRef = useRef(null);

  const prependIndex = index.length > 0 && typeof index[0] === 'string';
  const options = {
    data: prependIndex ? data.map((row, i) => [index[i]].concat(row)) : data,
    columns: (prependIndex ? [{ title: 'Time', width: 100, type: 'string' }] : []).concat(
      columns.map((title) => ({ title: String(title), width: 100, type: 'number' })),
    ),
  };

  useEffect(() => {
    if (jRef === null) return;

    const { current } = jRef;
    if (current === null) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if (!(current as any).jspreadsheet) {
      jspreadsheet(jRef.current, options);
    }
  }, [options]);

  return (
    <div>
      <div ref={jRef} />
    </div>
  );
}
*/
export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { data = [], columns = [], index = [] } = props.data;
  const prependIndex = index.length > 0 && typeof index[0] === 'string';
  const [grid, setGrid] = useState<Array<CellType>>([]);

  useEffect(() => {
    const columns_data: CellType = (prependIndex ? [{ value: 'Time', readOnly: true }] : []).concat(
      columns.map((title) => ({ value: String(title), readOnly: true })),
    );
    const tmp_grid = [columns_data];
    const tmp_data = data.map((row, i) => {
      const tmp_row = row.map((item) => ({ value: item, readOnly: false }));

      return (
        prependIndex ? [{ value: index[i], readOnly: true }].concat(tmp_row) : tmp_row
      );
    });
    tmp_grid.concat(tmp_data);
    setGrid(tmp_grid.concat(tmp_data));
  }, [columns, data, index, prependIndex]);

  return (
    <div>
      <ReactDataSheet
        data={grid}
        valueRenderer={(cell) => cell.value}
        onCellsChanged={(changes) => {
          const new_grid = grid.map((row) => [...row]);
          changes.forEach(({ cell, row, col, value }) => {
            new_grid[row][col] = value ? { value, readOnly: false } : new_grid[row][col];
          });
          setGrid(new_grid);
        }}
      />
    </div>
  );
}
