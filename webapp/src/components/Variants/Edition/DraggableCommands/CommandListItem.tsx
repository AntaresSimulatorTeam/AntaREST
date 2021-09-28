// @flow
import React, { CSSProperties, useState } from 'react';
import clsx from 'clsx';
import { DraggableProvided } from 'react-beautiful-dnd';
import ReactJson, { InteractionProps } from 'react-json-view';
import DeleteIcon from '@material-ui/icons/HighlightOff';
import { Accordion, AccordionDetails, AccordionSummary, createStyles, makeStyles, Theme, Typography } from '@material-ui/core';
import ExpandMore from '@material-ui/icons/ExpandMore';
import SaveOutlinedIcon from '@material-ui/icons/SaveOutlined';
import { CommandItem } from '../CommandTypes';

const useStyles = makeStyles((theme: Theme) => createStyles({
  item: {
    boxSizing: 'border-box',
    display: 'flex',
    flexFlow: 'row nowrap',
    justifyContent: 'space-between',
    alignItems: 'center',
    width: '100%',
    height: 'auto',
    userSelect: 'none',
  },
  onTopVisible: {
    zIndex: 10000,
  },
  normalItem: {
    flex: 1,
    border: `1px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(0, 0.2),
    boxSizing: 'border-box',
  },
  draggingListItem: {
    flex: 1,
    borderColor: theme.palette.secondary.main,
    boxShadow: `0px 0px 2px rgb(8, 58, 30), 0px 0px 10px ${theme.palette.secondary.main}`,
  },
  deleteIcon: {
    flex: '0 0 24px',
    color: theme.palette.error.light,
    marginLeft: theme.spacing(1),
    marginRight: theme.spacing(1),
    cursor: 'pointer',
    '&:hover': {
      color: theme.palette.error.main,
    },
  },
  infos: {
    display: 'flex',
    flexFlow: 'column nowrap',
    justifyContent: 'flex-start',
    alignItems: 'flex-start',
    boxSizing: 'border-box',
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
    boxSizing: 'border-box',
    padding: theme.spacing(0, 1),
  },
  headerIcon: {
    width: '24px',
    height: 'auto',
    cursor: 'pointer',
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
    zIndex: 999, // for json edition modal to be up everything else
  },
}));

interface StyleType {
    provided: DraggableProvided;
    style: CSSProperties;
    isDragging: boolean;
}
function getStyle({ provided, style, isDragging }: StyleType) {
  // If you don't want any spacing between your items
  // then you could just return this.
  // I do a little bit of magic to have some nice visual space
  // between the row items
  const combined = {
    ...style,
    ...provided.draggableProps.style,
  };

  const marginBottom = 8;
  const withSpacing = {
    ...combined,
    height: isDragging ? combined.height : (combined.height as number) - marginBottom,
    marginBottom,
  };
  return withSpacing;
}

interface PropsType {
    provided: DraggableProvided;
    item: CommandItem;
    style: CSSProperties;
    isDragging: boolean;
    index: number;
    onDelete: (index: number) => void;
    onArgsUpdate: (index: number, json: object) => void;
    onSave: (index: number) => void;
}

function Item({ provided, item, style, isDragging, index, onDelete, onArgsUpdate, onSave }: PropsType) {
  const classes = useStyles();
  const [jsonData, setJsonData] = useState<object>(item.args);
  const [isExpanded, setExpanded] = useState<boolean>(false);

  const updateJson = (e: InteractionProps) => {
    setJsonData(e.updated_src);
    onArgsUpdate(index, e.updated_src);
  };
  return (
    <div
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.draggableProps}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      className={isExpanded ? clsx(classes.item, classes.onTopVisible) : classes.item}
    >
      <Accordion
        className={isDragging ? classes.draggingListItem : classes.normalItem}
      >
        <AccordionSummary
          expandIcon={<ExpandMore />}
          aria-controls="panel1a-content"
          id="panel1a-header"
          style={{ width: '90%' }}
          onClick={() => setExpanded(!isExpanded)}
        >
          <div className={classes.infos}>
            <Typography color="primary" style={{ fontSize: '0.9em' }}>{item.action}</Typography>
            <Typography style={{ fontSize: '0.8em', color: 'gray' }}>{item.id}</Typography>
          </div>
        </AccordionSummary>
        <AccordionDetails className={classes.details}>
          <div className={classes.details}>
            <div className={classes.header}>
              {item.updated && <SaveOutlinedIcon className={classes.headerIcon} onClick={() => onSave(index)} />}
              {
                   // <CloudDownloadOutlinedIcon className={classes.headerIcon} />
                   // <CloudUploadOutlinedIcon className={classes.headerIcon} />
                  }
            </div>
            <div className={classes.json}>
              <ReactJson src={jsonData} onEdit={updateJson} onDelete={updateJson} onAdd={updateJson} />
            </div>
          </div>
        </AccordionDetails>
      </Accordion>
      <DeleteIcon className={classes.deleteIcon} onClick={() => onDelete(index)} />
    </div>
  );
}

export default Item;
