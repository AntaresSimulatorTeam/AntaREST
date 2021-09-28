// @flow
import React, { CSSProperties, useState } from 'react';
import { DraggableProvided } from 'react-beautiful-dnd';
import { createStyles, makeStyles, Theme } from '@material-ui/core';
import { CommandItem } from '../CommandTypes';

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

  isDragging: {
    background: '#515b7d',
    borderColor: 'MediumSeaGreen',
    boxShadow: '0px 0px 2px rgb(8, 58, 30), 0px 0px 10px MediumSeaGreen',
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

function TestItem({ provided, item, style, isDragging, index, onDelete, onArgsUpdate, onSave }: PropsType) {
  const classes = useStyles();
  return (
    <div
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.draggableProps}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...provided.dragHandleProps}
      ref={provided.innerRef}
      style={getStyle({ provided, style, isDragging })}
      className={isDragging ? classes.isDragging : classes.item}
    >
      {item.action}
      :
      {item.id}
    </div>
  );
}

export default TestItem;
