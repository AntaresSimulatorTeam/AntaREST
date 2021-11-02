import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { createStyles, makeStyles, Theme, InputLabel, FormControl, Box, OutlinedInput, Chip, Select, MenuItem, FormControlLabel, Checkbox } from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { MatrixType } from '../../../common/types';
import 'handsontable/dist/handsontable.min.css';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    height: '100%',
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
    display: 'flex',
    alignItems: 'center',
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
  monotonous: {
    marginLeft: theme.spacing(2),
  },
  autosizer: {
    display: 'block',
    width: '100%',
    height: '100%',
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
  const [monotonous, setMonotonous] = useState<boolean>(false);

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setColumnName(event.target.value as string[]);
  };

  const monotonousChange = () => {
    setMonotonous(!monotonous);
  };

  const unitChange = (tabBase: Array<number>) => {
    const tab = [...tabBase];
    for (let i = 0; i < tab.length; i += 1) {
      if (i === 0) {
        tab.splice(i, 1, 100 / tab.length);
      } else {
        tab.splice(i, 1, 100 / tab.length + tab[i - 1]);
      }
    }
    return tab;
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
        <FormControlLabel
          className={classes.monotonous}
          control={(
            <Checkbox
              checked={monotonous}
              onChange={monotonousChange}
              name="checked"
              color="primary"
            />
          )}
          label="Affichage Monotone"
        />
      </div>
      <div className={classes.autosizer}>
        <AutoSizer>
          {
            ({ height, width }) => (
              <Plot
                data={columnName.map((val, i) => (
                  {
                    x: monotonous ? unitChange(index as Array<number>) : index,
                    y: monotonous ? data.map((a) => a[i]).sort((b, c) => c - b) : data.map((a) => a[i]),
                    mode: 'lines',
                  }
                ))}
                layout={{ width, height }}
              />
            )
          }
        </AutoSizer>
      </div>
    </div>
  );
}
