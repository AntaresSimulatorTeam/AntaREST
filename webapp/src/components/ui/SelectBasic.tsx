import React from 'react';
import {
  makeStyles,
  createStyles,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles(() =>
  createStyles({
    formControl: {
      minWidth: '100%',
    },
  }));

type onChangeType = () => void;

interface PropType {
  items: Array<string>;
  label: string;
  name: string;
  value: string;
  optional?: boolean;
  variant?: 'filled' | 'standard' | 'outlined' | undefined;
  handleChange: (key: string, value: string | number) => void;
}

const SelectBasic = (props: PropType) => {
  const { items, label, name, value, optional, variant, handleChange } = props;
  const classes = useStyles();
  const [t] = useTranslation();

  return (
    <FormControl variant={variant} className={classes.formControl}>
      <InputLabel id={`${label}-label`}>{name}</InputLabel>
      <Select
        labelId={`${label}-label`}
        id={`${label}-select-filled`}
        value={value}
        onChange={(e) => handleChange(label, e.target.value as string)}
      >
        {optional &&
          <MenuItem value="" key="None">{t('main:none')}</MenuItem>
        }
        {items.map((item) => (
          <MenuItem value={item} key={item}>{item}</MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

SelectBasic.defaultProps = {
  optional: false,
  variant: 'filled',
};

export default SelectBasic;
