import * as React from 'react';
import {
  DragDropContext,
  Droppable,
  Draggable,
  DraggableProvided,
  DraggableStateSnapshot,
  OnDragEndResponder,
} from 'react-beautiful-dnd';
import { areEqual, FixedSizeList, VariableSizeList, ListChildComponentProps } from 'react-window';
import { Container } from '@material-ui/core';
import { useEffect, useRef } from 'react';
import CommandListItem from './CommandItem';
import { CommandItem } from '../CommandTypes';

export type DraggableListProps = {
  items: CommandItem[];
  onDragEnd: OnDragEndResponder;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
};

type RowProps = {
  items: Array<CommandItem>;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
};

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const { items, onDelete, onArgsUpdate, onSave } = data;
  const item = items[index];
  return (
    <Draggable draggableId={item.id as string} index={index} key={(item.id as string)}>
      {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => <CommandListItem style={style} provided={provided} snapshot={snapshot} item={item} index={index} onDelete={onDelete} onArgsUpdate={onArgsUpdate} onSave={onSave} />}
    </Draggable>
  );
});

const CommandListView = React.memo(({ items, onDragEnd, onDelete, onArgsUpdate, onSave }: DraggableListProps) => (
  <DragDropContext onDragEnd={onDragEnd}>
    <Droppable
      droppableId="droppable-list"
      mode="virtual"
      renderClone={(provided, snapshot, rubric) => (
        <CommandListItem
          provided={provided}
          snapshot={snapshot}
          item={items[rubric.source.index]}
          index={rubric.source.index}
          onDelete={onDelete}
          onArgsUpdate={onArgsUpdate}
          onSave={onSave}
        />
      )}
    >
      {(provided, snapshot) => {
        // eslint-disable-next-line react/jsx-props-no-spreading
        const itemCount = snapshot.isUsingPlaceholder
          ? items.length + 1
          : items.length;

        return (
          <FixedSizeList
            height={500}
            itemCount={itemCount}
            itemSize={30}
            width="100%"
            outerRef={provided.innerRef}
          // eslint-disable-next-line react/jsx-props-no-spreading
            {...provided.droppableProps}
            itemData={{ items, onDelete, onArgsUpdate, onSave }}
            style={{ width: '100%', height: '100%', backgroundColor: 'black', overflowY: 'auto' }}
          >
            {Row}
          </FixedSizeList>
        );
      }}
    </Droppable>
  </DragDropContext>
));

export default CommandListView;
