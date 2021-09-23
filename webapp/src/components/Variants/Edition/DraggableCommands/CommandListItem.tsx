import * as React from 'react';
import { Draggable } from 'react-beautiful-dnd';
import ReactJson from 'react-json-view';
import { Accordion, AccordionDetails, AccordionSummary, createStyles, Theme, Typography } from '@material-ui/core';
import makeStyles from '@material-ui/core/styles/makeStyles';
import ExpandMore from '@material-ui/icons/ExpandMore';
import CloudDownloadOutlinedIcon from '@material-ui/icons/CloudDownloadOutlined';
import CloudUploadOutlinedIcon from '@material-ui/icons/CloudUploadOutlined';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import { CommandItem } from '../CommandTypes';

const useStyles = makeStyles((theme: Theme) => createStyles({
  container: {
    boxSizing: 'border-box',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    backgroundColor: 'blue',
  },
  normalItem: {
    border: `1px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(0.2, 0.2),
    boxSizing: 'border-box',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    backgroundColor: 'blue',
  },
  draggingListItem: {
    background: 'rgb(235,235,235)',
  },
  details: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  header: {
    width: '100%',
    height: '50px',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'flex-end',
    alignItems: 'center',
    padding: theme.spacing(0, 1),
  },
  headerIcon: {
    width: '24px',
    height: 'auto',
    color: theme.palette.primary.main,
    margin: theme.spacing(0, 0.5),
    '&:hover': {
      color: theme.palette.secondary.main,
    },
  },
  json: {
    width: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
  },
  deleteIcon: {
    color: theme.palette.error.light,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
}));

export type DraggableListItemProps = {
  item: CommandItem;
  index: number;
  onDelete: (index: number) => void;
};

const CommandListItem = ({ item, index, onDelete }: DraggableListItemProps) => {
  const classes = useStyles();
  /*  NOTE:
      Example Json will be the command model corresponding to CommandItem
      This model will exist in redux store
      Model for all commands will be fetched at the begining and stored in a redux store
  */
  const exampleJson = {
    Test1: 'Hey 1',
    Test2: 'Hey 2',
    'Test 3': {
      'Test 4': 'Hey 3',
      'Test 5': 'Hey 4',
    },
    'Test 6': 'Hey 5',
  };

  return (
    <Draggable draggableId={item.name} index={index}>
      {(provided, snapshot) => (
        <div
          className={classes.container}
          ref={provided.innerRef}
        // eslint-disable-next-line react/jsx-props-no-spreading
          {...provided.draggableProps}
        // eslint-disable-next-line react/jsx-props-no-spreading
          {...provided.dragHandleProps}
        >
          <Accordion
            className={snapshot.isDragging ? classes.draggingListItem : classes.normalItem}
          >
            <AccordionSummary
              expandIcon={<ExpandMore />}
              aria-controls="panel1a-content"
              id="panel1a-header"
            >
              <Typography>{item.name}</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <div className={classes.details}>
                <div className={classes.header}>
                  <CloudDownloadOutlinedIcon className={classes.headerIcon} />
                  <CloudUploadOutlinedIcon className={classes.headerIcon} />
                </div>
                <div className={classes.json}>
                  <ReactJson src={exampleJson} />
                </div>
              </div>
            </AccordionDetails>
          </Accordion>
          <DeleteIcon className={classes.deleteIcon} onClick={() => onDelete(index)} />
        </div>
      )}
    </Draggable>
  );
};

export default CommandListItem;
