import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { createStyles, makeStyles, Theme, InputLabel, FormControl, Box, OutlinedInput, Chip, Select, MenuItem } from '@material-ui/core';
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

  form: {
    minWidth: '200px',
    marginTop: theme.spacing(1),
    marginBottom: theme.spacing(1),
  },
  input: {
    top: '-7px',
    left: '14px',
  },
  container: {
    width: '100%',
  },
  box: {
    marginRight: theme.spacing(1),
    height: '24px',
    '& span': {
      padding: '8px',
    },
  },
  select: {
    '& .MuiSelect-select': {
      paddingBottom: theme.spacing(1) + 4,
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
  const [columnName, setColumnName] = useState<string[]>([]);

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setColumnName(event.target.value as string[]);
  };

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        <FormControl className={classes.form}>
          <InputLabel className={classes.input} id="demo-multiple-chip-label">Col</InputLabel>
          <Select
            className={classes.select}
            labelId="demo-multiple-chip-label"
            id="demo-multiple-chip"
            multiple
            value={columnName}
            onChange={handleChange}
            input={<OutlinedInput id="select-multiple-chip" label="Col" />}
            renderValue={(selected) => (
              <Box>
                {(selected as string[]).map((value) => (
                  <Chip className={classes.box} key={value} label={value} />
                ))}
              </Box>
            )}
          >
            {columns.map((column) => (
              <MenuItem
                key={column}
                value={column}
              >
                {column}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </div>
      <Plot
        data={columnName.map((val, i) => (
          {
            x: index,
            y: data.map((a) => a[i]),
            mode: 'lines',
          }
        ))}
        layout={{ width: 691, height: 518 }}
      />
    </div>
  );
}
