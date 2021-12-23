import React, { useEffect, useState } from 'react';
import { Graph } from 'react-d3-graph';
import {
  makeStyles,
  createStyles,
  Theme,
  Paper,
  Typography,
} from '@material-ui/core';
import { useTranslation } from 'react-i18next';

const useStyles = makeStyles((theme: Theme) =>
  createStyles({
    root: {
      width: '100%',
      height: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: 'white',
      margin: theme.spacing(1),
      boxSizing: 'border-box',
    },
    header: {
      width: '100%',
      height: '40px',
      boxSizing: 'border-box',
      display: 'flex',
      flexFlow: 'row nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      backgroundColor: theme.palette.primary.main,
      borderTopLeftRadius: theme.shape.borderRadius,
      borderTopRightRadius: theme.shape.borderRadius,
      paddingLeft: theme.spacing(2),
    },
    title: {
      fontWeight: 'bold',
      color: 'white',
    },
    main: {
      flex: 1,
      width: '100%',
      display: 'flex',
      flexFlow: 'column nowrap',
      justifyContent: 'flex-start',
      alignItems: 'center',
      position: 'relative',
    },
  }));

interface Props {
    studyId: string;
}

const data = {
  nodes: [{ id: 'Harry' }, { id: 'Sally' }, { id: 'Alice' }],
  links: [
    { source: 'Harry', target: 'Sally' },
    { source: 'Harry', target: 'Alice' },
  ],
};

const myConfig = {
  initialZoom: 5,
  height: 700,
  width: 1000,
  d3: {
    linkLength: 100,
  },
  node: {
    color: '#d3d3d3',
    size: 200,
  },
  link: {
    color: '#d3d3d3',
  },
};

const NoteView = (props: Props) => {
  const classes = useStyles();
  const [t] = useTranslation();
  const { studyId } = props;

  const onClickNode = (nodeId: string) => {
    console.log(`Clicked node ${nodeId}`);
  };

  const onClickLink = (source: string, target: string) => {
    console.log(`Clicked link between ${source} and ${target}`);
  };

  return (
    <Paper className={classes.root}>
      <div className={classes.header}>
        <Typography className={classes.title}>Map</Typography>
      </div>
      <div className={classes.main}>
        <Graph
          id="graph-id" // id is mandatory
          data={data}
          config={myConfig}
          onClickNode={onClickNode}
          onClickLink={onClickLink}
        />
      </div>
    </Paper>
  );
};

export default NoteView;
