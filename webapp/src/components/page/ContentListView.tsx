/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import { Box } from "@mui/material";
import { useState } from "react";
import { useUpdateEffect } from "react-use";
import ListPanel, { type ListPanelItem } from "../ListPanel";
import SplitView, { type SplitViewProps } from "./SplitView";

export interface ContentListItem<TData = unknown> extends ListPanelItem {
  /**
   * It will be used in priority over `renderItemContent` if provided.
   */
  content?: React.ReactNode;
  /**
   * Used in `renderItemContent` when `content` is not provided.
   */
  data?: TData;
}

interface ListViewProps<TItemData = unknown> {
  list: Array<ContentListItem<TItemData>>;
  splitId: SplitViewProps["splitId"];
  splitMinSize?: SplitViewProps["minSize"];
  emptyListContent?: React.ReactNode;
  onAdd?(): void;
  actions?: React.ReactNode;
  renderItemContent?: (item: { id: ListPanelItem["id"]; data?: TItemData }) => React.ReactNode;
}

function ListView<TItemData>({
  list,
  splitId,
  splitMinSize,
  emptyListContent,
  onAdd,
  actions,
  renderItemContent,
}: ListViewProps<TItemData>) {
  const [activeItem, setActiveItem] = useState(list[0]);

  // Ensure there's always an active item selected
  useUpdateEffect(() => {
    if (!activeItem || !list.find((item) => item.id === activeItem.id)) {
      setActiveItem(list[0]);
    }
  }, [activeItem, list]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const renderItemView = () => {
    if (list.length === 0) {
      return emptyListContent;
    }

    if (activeItem) {
      return (
        activeItem.content || renderItemContent?.({ id: activeItem.id, data: activeItem.data })
      );
    }

    return null;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView splitId={splitId} minSize={splitMinSize}>
      <ListPanel
        list={list}
        onAdd={onAdd}
        actions={actions}
        itemButtonProps={(item) => ({
          onClick: () => setActiveItem(item),
          selected: activeItem?.id === item.id,
        })}
      />
      <Box>{renderItemView()}</Box>
    </SplitView>
  );
}

export default ListView;
