/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import { memo, useEffect, useRef } from "react";
import { FixedSizeList, areEqual, type ListChildComponentProps } from "react-window";
import {
  DragDropContext,
  Droppable,
  Draggable,
  type OnDragEndResponder,
} from "react-beautiful-dnd";
import type { CommandItem } from "../commandTypes";
import CommandListItem from "./CommandListItem";

const Row = memo((props: ListChildComponentProps) => {
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

Row.displayName = "Row";

export interface DraggableListProps {
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
}

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
      if (generationIndex >= 0) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (listRef.current as any).scrollToItem(generationIndex, "smart");
      }
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
          <FixedSizeList
            height={1000}
            itemCount={items.length}
            itemSize={80}
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
              height: "100%",
            }}
          >
            {Row}
          </FixedSizeList>
        )}
      </Droppable>
    </DragDropContext>
  );
}

export default CommandListView;
