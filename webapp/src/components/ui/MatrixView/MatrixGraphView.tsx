import React from 'react';
import Plot from 'react-plotly.js';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { MatrixType } from '../../../common/types';
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
  buttongroup: {
    width: '100%',
  },
  button: {
    marginBottom: theme.spacing(3),
  },
  disable: {
    backgroundColor: '#002a5e !important',
    color: 'white !important',
  },
  enable: {
    backgroundColor: 'rgba(0, 0, 0, 0.12)',
    color: 'rgba(0, 0, 0, 0.26)',
    '&:hover': {
      color: 'white',
    },
  },
}));

interface PropTypes {
  matrix: MatrixType;
}

export default function MatrixGraphView(props: PropTypes) {
  // eslint-disable-next-line react/destructuring-assignment
  const { matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const classes = useStyles();

  return (
    <div className={classes.root}>
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
    </div>
  );
}
