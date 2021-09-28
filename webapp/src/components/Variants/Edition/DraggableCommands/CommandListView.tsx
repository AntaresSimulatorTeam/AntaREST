import React from 'react';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import { DragDropContext, Droppable, Draggable, OnDragEndResponder } from 'react-beautiful-dnd';
import { CommandItem } from '../CommandTypes';
import CommandListItem from './CommandListItem';

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { items, onDelete, onArgsUpdate, onSave } = data;
  const item = items[index];
  return (
    <Draggable draggableId={item.id} index={index} key={item.id}>
      {(provided, snapshot) => <CommandListItem provided={provided} isDragging={snapshot.isDragging} item={item} style={style} index={index} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} />}
    </Draggable>
  );
}, areEqual);

export type DraggableListProps = {
  items: CommandItem[];
  onDragEnd: OnDragEndResponder;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
};

function CommandListView({ items, onDragEnd, onDelete, onArgsUpdate, onSave }: DraggableListProps) {
  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable
        droppableId="droppable"
        mode="virtual"
        renderClone={(provided, snapshot, rubric) => (
          <CommandListItem
            provided={provided}
            isDragging={snapshot.isDragging}
            item={items[rubric.source.index]}
            index={rubric.source.index}
            onDelete={onDelete}
            onArgsUpdate={onArgsUpdate}
            onSave={onSave}
            style={{}}
          />
        )}
      >
        {(provided) => (
          <FixedSizeList
            height={500}
            itemCount={items.length}
            itemSize={80}
            width={300}
            outerRef={provided.innerRef}
            itemData={{ items, onDelete, onArgsUpdate, onSave }}
            style={{ width: '100%', height: '90%' }}
          >
            {Row}
          </FixedSizeList>
        )}
      </Droppable>
    </DragDropContext>
  );
}

export default CommandListView;
