import * as React from 'react';
import { Draggable } from 'react-beautiful-dnd';
import { createStyles, Theme } from '@material-ui/core';
import makeStyles from '@material-ui/core/styles/makeStyles';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import { CommandDTO } from '../../../../common/types';

const useStyles = makeStyles((theme: Theme) => createStyles({
  normalItem: {
    border: `1px solid ${theme.palette.primary.main}`,
    margin: theme.spacing(0.2, 0.2),
    boxSizing: 'border-box',
  },
  draggingListItem: {
    background: 'rgb(235,235,235)',
  },
}));

export type DraggableListItemProps = {
  item: CommandDTO;
  index: number;
};

const CommandListItem = ({ item, index }: DraggableListItemProps) => {
  const classes = useStyles();
  return (
    <Draggable draggableId={item.name} index={index}>
      {(provided, snapshot) => (
        <ListItem
          ref={provided.innerRef}
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...provided.draggableProps}
          // eslint-disable-next-line react/jsx-props-no-spreading
          {...provided.dragHandleProps}
          className={snapshot.isDragging ? classes.draggingListItem : classes.normalItem}
        >
          <ListItemText primary={item.action} secondary={item.name} />
        </ListItem>
      )}
    </Draggable>
  );
};

export default CommandListItem;
