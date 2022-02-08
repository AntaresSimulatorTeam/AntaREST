/* eslint-disable @typescript-eslint/camelcase */
import React, { useState } from 'react';
import { Chip, createStyles, makeStyles, TextField, Theme } from '@material-ui/core';
import AddCircleOutlinedIcon from '@material-ui/icons/AddCircleOutlined';

const useStyles = makeStyles((theme: Theme) => createStyles({
  root: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    padding: 0,
  },
  inputContainer: {
    width: '100%',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-end',
    padding: 0,
    marginBottom: theme.spacing(1),
  },
  tagContainer: {
    display: 'flex',
    border: 0,
    backgroundColor: '#00000000',
    justifyContent: 'center',
    flexWrap: 'wrap',
    listStyle: 'none',
    padding: theme.spacing(0.5),
    margin: 0,
  },
  chip: {
    margin: theme.spacing(0.5),
  },
  addIcon: {
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 1),
    cursor: 'pointer',
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
}));

interface PropTypes {
    label: string;
    values: Array<string>;
    onChange: (value: Array<string>) => void;
}

const TagSelect = (props: PropTypes) => {
  const classes = useStyles();
  const { label, values, onChange } = props;
  const [value, setValue] = useState<string>('');

  const onAddTag = (): void => {
    if (values.findIndex((elm) => elm === value) < 0 && value !== '') {
      onChange(values.concat(value));
      setValue('');
    }
  };

  return (
    <div className={classes.root} style={{ marginBottom: 0 }}>
      <div className={classes.inputContainer} style={{ alignItems: 'center' }}>
        <TextField label={label} value={value} onChange={(event) => setValue(event.target.value)} style={{ marginLeft: '5px', marginRight: '5px', flex: 1 }} />
        <AddCircleOutlinedIcon className={classes.addIcon} onClick={onAddTag} />
      </div>
      <ul className={classes.tagContainer}>
        {values.map((elm) => (
          <li key={elm}>
            <Chip
              label={elm}
              onDelete={() => onChange(values.filter((item) => item !== elm))}
              className={classes.chip}
            />
          </li>
        ))}
      </ul>
    </div>
  );
};

export default TagSelect;
