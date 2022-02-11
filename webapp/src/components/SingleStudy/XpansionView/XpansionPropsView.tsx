import React from 'react';
import {
  makeStyles,
  createStyles,
  Theme,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';
import PropertiesView from '../../ui/PropertiesView';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    list: {
      minWidth: '75%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'flex-start',
    },
    prevButton: {
      color: theme.palette.primary.main,
    },
  }));

interface PropsType {
  candidateList: Array<string>;
  onAdd: () => void;
}

const XpansionPropsView = (props: PropsType) => {
  const classes = useStyles();
  const { candidateList, onAdd } = props;
  const [t] = useTranslation();

  return (
    <PropertiesView
      content={candidateList}
      filter={
        <>Filtered</>
      }
      onChange={() => console.log('search')}
      onAdd={onAdd}
    />
  );
};

export default XpansionPropsView;
