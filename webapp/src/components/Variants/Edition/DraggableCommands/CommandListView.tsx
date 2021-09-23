import * as React from 'react';
import {
  DragDropContext,
  Droppable,
  OnDragEndResponder,
} from 'react-beautiful-dnd';
import CommandListItem from './CommandListItem';
import { CommandItem } from '../CommandTypes';

export type DraggableListProps = {
  items: CommandItem[];
  onDragEnd: OnDragEndResponder;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
};

const CommandListView = React.memo(({ items, onDragEnd, onDelete, onArgsUpdate }: DraggableListProps) => (
  <DragDropContext onDragEnd={onDragEnd}>
    <Droppable droppableId="droppable-list">
      {(provided) => (
        // eslint-disable-next-line react/jsx-props-no-spreading
        <div ref={provided.innerRef} {...provided.droppableProps} style={{ paddingTop: '10px', paddingBottom: '10px' }}>
          {items.map((item, index) => (
            <CommandListItem item={item} index={index} key={item.name} onDelete={onDelete} onArgsUpdate={onArgsUpdate} />
          ))}
          {provided.placeholder}
        </div>
      )}
    </Droppable>
  </DragDropContext>
));

export default CommandListView;
