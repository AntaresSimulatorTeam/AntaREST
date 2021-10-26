import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { HotTable, HotColumn } from '@handsontable/react';
import { createStyles, makeStyles, ButtonGroup, Button } from '@material-ui/core';
import { MatrixType } from '../../common/types';
import 'handsontable/dist/handsontable.min.css';

const useStyles = makeStyles(() => createStyles({
  root: {
    width: '100%',
    height: '100%',
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
  },
}));

interface PropTypes {
  matrix: MatrixType;
  readOnly: boolean;
}

type CellType = Array<number | string | boolean>;
type ColumnsType = {title: string; readOnly: boolean};

export default function MatrixView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { readOnly, matrix } = props;
  console.log(matrix);
  const { data = [], columns = [], index = [] } = matrix;
  const classes = useStyles();
  const prependIndex = index.length > 0 && typeof index[0] === 'string';
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);

  useEffect(() => {
    const columnsData: Array<ColumnsType> = (prependIndex ? [{ title: 'Time', readOnly }] : []).concat(
      columns.map((title) => ({ title: String(title), readOnly })),
    );
    setColumns(columnsData);

    const tmpData = data.map((row, i) => (
      prependIndex ? [index[i]].concat(row) : row
    ));
    setGrid(tmpData);
  }, [columns, data, index, prependIndex, readOnly]);

  console.log(data.map((a) => a[0]));
  console.log(index);
  /*      
            <Plot
        data={[
          {
            x: index,
            y: data.map((a) => a[0]),
            type: 'scatter',
            mode: 'lines',
            marker: { color: 'red' },
          },
        ]}
        layout={{ width: 960, height: 720 }}
      />*/
  return (
    <div className={classes.root}>
      <ButtonGroup variant="contained">
        <Button>One</Button>
        <Button>Two</Button>
      </ButtonGroup>
      <HotTable
        data={grid}
        licenseKey="non-commercial-and-evaluation"
        width="100%"
        height="100%"
      >
        {
          formatedColumns.map((column) =>
            <HotColumn key={column.title} settings={column} />)
        }
      </HotTable>
    </div>
  );
}
