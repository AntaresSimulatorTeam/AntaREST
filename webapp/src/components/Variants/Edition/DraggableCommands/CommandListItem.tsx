import React, { useState } from 'react';
import { Draggable } from 'react-beautiful-dnd';
import ReactJson, { InteractionProps } from 'react-json-view';
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
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    height: 'auto',
  },
  normalItem: {
    flex: 1,
    border: `1px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(0, 0.2),
    boxSizing: 'border-box',
  },
  draggingListItem: {
    flex: 1,
    background: 'rgb(235,235,235)',
  },
  details: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'center',
    boxSizing: 'border-box',
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
    flex: '0 0 24px',
    color: theme.palette.error.light,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
  infos: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
  },
}));

export type DraggableListItemProps = {
  item: CommandItem;
  index: number;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
};

const CommandListItem = ({ item, index, onDelete, onArgsUpdate }: DraggableListItemProps) => {
  const classes = useStyles();
  const [jsonData, setJsonData] = useState<object>(item.args);

  const updateJson = (e: InteractionProps) => {
    setJsonData(e.updated_src);
    onArgsUpdate(index, e.updated_src);
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
              style={{ width: '90%' }}
            >
              <div className={classes.infos}>
                <Typography color="primary" style={{ fontSize: '0.9em' }}>{item.action}</Typography>
                <Typography style={{ fontSize: '0.8em', color: 'gray' }}>{item.name}</Typography>
              </div>
            </AccordionSummary>
            <AccordionDetails className={classes.details}>
              <div className={classes.details}>
                <div className={classes.header}>
                  <CloudDownloadOutlinedIcon className={classes.headerIcon} />
                  <CloudUploadOutlinedIcon className={classes.headerIcon} />
                </div>
                <div className={classes.json}>
                  <ReactJson src={jsonData} onEdit={updateJson} onDelete={updateJson} onAdd={updateJson} />
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
