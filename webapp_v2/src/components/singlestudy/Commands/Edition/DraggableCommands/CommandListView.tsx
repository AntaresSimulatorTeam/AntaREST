import React, { useEffect, useRef } from "react";
import { FixedSizeList, areEqual, ListChildComponentProps } from "react-window";
import {
  DragDropContext,
  Droppable,
  Draggable,
  OnDragEndResponder,
} from "react-beautiful-dnd";
import { styled } from "@mui/material";
import { CommandItem } from "../commandTypes";
import CommandListItem from "./CommandListItem";
import { scrollbarStyle } from "../../../../../theme";

const StyledList = styled(FixedSizeList)(({ theme }) => ({
  ...scrollbarStyle,
}));

const Row = React.memo((props: ListChildComponentProps) => {
  const { data, index, style } = props;
  const {
    items,
    onDelete,
    onArgsUpdate,
    onSave,
    onCommandImport,
    onCommandExport,
    onExpanded,
    expandedIndex,
    generationStatus,
    generationIndex,
  } = data;
  const item = items[index];
  return (
    <Draggable draggableId={item.id} index={index} key={item.id}>
      {(provided, snapshot) => (
        <CommandListItem
          provided={provided}
          isDragging={snapshot.isDragging}
          item={item}
          style={style}
          index={index}
          expandedIndex={expandedIndex}
          generationStatus={generationStatus}
          generationIndex={generationIndex}
          onDelete={onDelete}
          onArgsUpdate={onArgsUpdate}
          onSave={onSave}
          onCommandImport={onCommandImport}
          onCommandExport={onCommandExport}
          onExpanded={onExpanded}
        />
      )}
    </Draggable>
  );
}, areEqual);

export type DraggableListProps = {
  items: CommandItem[];
  generationStatus: boolean;
  generationIndex: number;
  onDragEnd: OnDragEndResponder;
  onDelete: (index: number) => void;
  onArgsUpdate: (index: number, json: object) => void;
  onSave: (index: number) => void;
  onCommandImport: (index: number, json: object) => void;
  onCommandExport: (index: number) => void;
  onExpanded: (index: number, value: boolean) => void;
  expandedIndex: number;
};

function CommandListView({
  items,
  generationStatus,
  generationIndex,
  expandedIndex,
  onDragEnd,
  onDelete,
  onArgsUpdate,
  onSave,
  onCommandImport,
  onCommandExport,
  onExpanded,
}: DraggableListProps) {
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef && listRef !== null && listRef.current) {
      if (generationIndex >= 0)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (listRef.current as any).scrollToItem(generationIndex, "smart");
    }
  }, [generationIndex]);

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <Droppable
        droppableId="droppable"
        isDropDisabled={generationStatus}
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
            onCommandImport={onCommandImport}
            onCommandExport={onCommandExport}
            generationStatus={generationStatus}
            generationIndex={generationIndex}
            expandedIndex={expandedIndex}
            onExpanded={onExpanded}
            style={{}}
          />
        )}
      >
        {(provided) => (
          <StyledList
            height={500}
            itemCount={items.length}
            itemSize={68}
            width={300}
            outerRef={provided.innerRef}
            ref={listRef}
            itemData={{
              items,
              onDelete,
              onArgsUpdate,
              onSave,
              onCommandImport,
              onCommandExport,
              onExpanded,
              generationStatus,
              generationIndex,
              expandedIndex,
            }}
            style={{
              width: "100%",
              height: "90%",
            }}
          >
            {Row}
          </StyledList>
        )}
      </Droppable>
    </DragDropContext>
  );
}

export default CommandListView;
