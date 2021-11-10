import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { createStyles, makeStyles, Theme, InputLabel, FormControl, Box, OutlinedInput, Chip, Select, MenuItem, FormControlLabel, Checkbox } from '@material-ui/core';
import AutoSizer from 'react-virtualized-auto-sizer';
import { useTranslation } from 'react-i18next';
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
    minWidth: '100px',
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
      minWidth: '100px',
    },
  },
  monotonic: {
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
  const [t] = useTranslation();
  const { matrix } = props;
  const { data = [], columns = [], index = [] } = matrix;
  const classes = useStyles();
  const [selectedColumns, setSelectedColumns] = useState<number[]>([]);
  const [monotonic, setMonotonic] = useState<boolean>(false);

  const handleChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedColumns(event.target.value as number[]);
  };

  const monotonicChange = () => {
    setMonotonic(!monotonic);
  };

  const unitChange = (tabBase: Array<number>) => {
    const stepLength = 100 / tabBase.length;
    return tabBase.map((el, i) => stepLength * (i + 1));
  };

  return (
    <div className={classes.root}>
      <div className={classes.container}>
        <FormControl className={classes.form}>
          <InputLabel className={classes.input} id="chip-label">{t('data:graphSelector')}</InputLabel>
          <Select
            className={classes.select}
            labelId="chip-label"
            id="matrix-chip"
            multiple
            value={selectedColumns}
            onChange={handleChange}
            input={<OutlinedInput id="select-chip" label={t('data:graphSelector')} />}
            renderValue={(selected) => (
              <Box>
                {(selected as number[]).map((value) => (
                  <Chip className={classes.box} key={value} label={columns[value]} />
                ))}
              </Box>
            )}
          >
            {columns.map((column, i) => (
              <MenuItem
                key={column}
                value={i}
              >
                {column}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControlLabel
          className={classes.monotonic}
          control={(
            <Checkbox
              checked={monotonic}
              onChange={monotonicChange}
              name="checked"
              color="primary"
            />
          )}
          label={t('data:monotonicView')}
        />
      </div>
      <div className={classes.autosizer}>
        <AutoSizer>
          {
            ({ height, width }) => (
              <Plot
                data={selectedColumns.map((val) => (
                  {
                    x: monotonic ? unitChange(index as Array<number>) : index,
                    y: monotonic ? data.map((a) => a[val]).sort((b, c) => c - b) : data.map((a) => a[val]),
                    mode: 'lines',
                    name: `${columns[val]}`,
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
