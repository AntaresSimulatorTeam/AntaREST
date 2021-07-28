import React from 'react';
import { createStyles, makeStyles, Theme } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import ArrowDropUpIcon from '@material-ui/icons/ArrowDropUp';
import ArrowDropDownIcon from '@material-ui/icons/ArrowDropDown';
import { SortStatus } from './utils';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      backgroundColor: '#00000000',
      border: 'none',
      color: theme.palette.primary.main,
      marginLeft: theme.spacing(0.5),
    },
  }));

  interface PropsType {
    status: SortStatus;
    label: string;
    onClick: () => void;
  }

const SortButton = (props: PropsType) => {
  const classes = useStyles(props);
  const { label, status, onClick } = props;

  const getIcon = (): JSX.Element => {
    switch (status) {
      case 'INCREASE':
        return <ArrowDropUpIcon />;

      case 'DECREASE':
        return <ArrowDropDownIcon />;
      default:
        return <></>;
    }
  };
  return (
    <Button
      className={classes.root}
      onClick={onClick}
      endIcon={getIcon()}
    >
      {label}
    </Button>
  );
};

export default SortButton;
