import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { HotTable, HotColumn } from '@handsontable/react';
import { createStyles, makeStyles, Theme, ButtonGroup, Button } from '@material-ui/core';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { MatrixType } from '../../common/types';
import 'handsontable/dist/handsontable.min.css';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  button: {
    marginTop: theme.spacing(3),
    marginBottom: theme.spacing(3),
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
  const { data = [], columns = [], index = [] } = matrix;
  const classes = useStyles();
  const prependIndex = index.length > 0 && typeof index[0] === 'string';
  const [grid, setGrid] = useState<Array<CellType>>([]);
  const [formatedColumns, setColumns] = useState<Array<ColumnsType>>([]);
  const [toggleView, setToggleView] = useState<boolean>(true);

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

  const renderHandleView = () => {
    if (toggleView) {
      return (
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
      );
    }
    return (
      <Plot
        data={columns.map((val, i) => (
          {
            x: index,
            y: data.map((a) => a[i]),
            type: 'scatter',
            mode: 'lines',
          }
        ))}
        layout={{ width: 960, height: 720 }}
      />
    );
  };

  const changeView = () => setToggleView(!toggleView);

  return (
    <div className={classes.root}>
      <ButtonGroup className={classes.button} variant="contained">
        {toggleView ? (
          <Button color="primary" disabled>
            <FontAwesomeIcon size="2x" icon="table" />
          </Button>
        ) : (
          <Button color="primary" onClick={changeView}>
            <FontAwesomeIcon size="2x" icon="table" />
          </Button>
        )}
        {toggleView ? (
          <Button color="primary" onClick={changeView}>
            <FontAwesomeIcon size="2x" icon="chart-area" />
          </Button>
        ) : (
          <Button color="primary" disabled>
            <FontAwesomeIcon size="2x" icon="chart-area" />
          </Button>
        )}
      </ButtonGroup>
      {renderHandleView()}
    </div>
  );
}
