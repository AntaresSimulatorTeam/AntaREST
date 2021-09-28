// @flow
import React, { CSSProperties, useState } from 'react';
import { FixedSizeList, areEqual, ListChildComponentProps } from 'react-window';
import { DragDropContext, Droppable, Draggable, DraggableProvided, DropResult } from 'react-beautiful-dnd';
import { createStyles, makeStyles, Theme } from '@material-ui/core';

const useStyles = makeStyles((theme: Theme) => createStyles({
  item: {
    background: '#333851',
    border: '4px solid mediumpurple',
    boxSizing: 'border-box',
    borderRadius: '8px',
    color: '#cdd5ee',
    fontSize: '30px',
    fontFamily: '"Vibur", cursive',
    userSelect: 'none',

    /* center align text */
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },

  itemIsDragging: {
    background: '#515b7d',
    borderColor: 'MediumSeaGreen',
    boxShadow: '0px 0px 2px rgb(8, 58, 30), 0px 0px 10px MediumSeaGreen',
  },
}));

// Generate our initial big data set
// Go on, make it 10,000 🤘
const initial = Array.from({ length: 1000 }, (v, k) => ({
  id: `id:${k}`,
  text: `item ${k}`,
}));

type ListType = {
    id: string;
    text: string;
}

function reorder(list: Array<ListType>, startIndex: number, endIndex: number) {
  const result = Array.from(list);
  const [removed] = result.splice(startIndex, 1);
  result.splice(endIndex, 0, removed);

  return result;
}

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

interface ItemType {
    provided: DraggableProvided;
    item: ListType;
    style: CSSProperties;
    isDragging: boolean;
}

function Item({ provided, item, style, isDragging }: ItemType) {
  return (
    <div
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.draggableProps}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      className={`item ${isDragging ? 'is-dragging' : ''}`}
    >
      {item.text}
    </div>
  );
}

// Recommended react-window performance optimisation: memoize the row render function
// Things are still pretty fast without this, but I am a sucker for making things faster
const Row = React.memo((props: ListChildComponentProps) => {
  const { data: items, index, style } = props;
  const item = items[index];
  return (
    <Draggable draggableId={item.id} index={index} key={item.id}>
      {(provided, snapshot) => <Item provided={provided} isDragging={snapshot.isDragging} item={item} style={style} />}
    </Draggable>
  );
}, areEqual);

function NewComponent() {
  const [items, setItems] = useState<Array<ListType>>(initial);

  function onDragEnd({ destination, source }: DropResult) {
    if (!destination) {
      return;
    }
    if (source.index === destination.index) {
      return;
    }

    const newItems: Array<ListType> = reorder(
      items,
      source.index,
      destination.index,
    );
    setItems(newItems);
  }

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable
        droppableId="droppable"
        mode="virtual"
        renderClone={(provided, snapshot, rubric) => (
          <Item
            provided={provided}
            isDragging={snapshot.isDragging}
            item={items[rubric.source.index]}
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
            itemData={items}
            style={{ width: '100%', height: 'auto', backgroundColor: 'red' }}
          >
            {Row}
          </FixedSizeList>
        )}
      </Droppable>
    </DragDropContext>
  );
}

export default NewComponent;
