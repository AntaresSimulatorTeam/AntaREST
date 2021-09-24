import * as React from 'react';
import {
  DragDropContext,
  Droppable,
  OnDragEndResponder,
} from 'react-beautiful-dnd';
import { Container } from '@material-ui/core';
import CommandListItem from './CommandListItem';
import { CommandItem } from '../CommandTypes';

export type DraggableListProps = {
  items: CommandItem[];
  onDragEnd: OnDragEndResponder;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
};

const CommandListView = React.memo(({ items, onDragEnd, onDelete, onArgsUpdate, onSave }: DraggableListProps) => (
  <DragDropContext onDragEnd={onDragEnd}>
    <Droppable droppableId="droppable-list">
      {(provided) => (
        // eslint-disable-next-line react/jsx-props-no-spreading
        <Container ref={provided.innerRef} {...provided.droppableProps}>
          {items.map((item, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <CommandListItem item={item} index={index} key={`${item.id}${index}`} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} />
          ))}
          {provided.placeholder}
        </Container>
      )}
    </Droppable>
  </DragDropContext>
));

export default CommandListView;
