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

import { Box, ListItemButton } from "@mui/material";
import { useState } from "react";
import { useUpdateEffect } from "react-use";
import ListPanel, { type ListPanelItem, type ListPanelProps } from "../../ListPanel";
import SplitView, { type SplitViewProps } from "../SplitView";
import { renderListItem } from "./utils";

export interface ListViewItem<TData = unknown> extends ListPanelItem {
  /**
   * It will be used in priority over `renderItemView` if provided.
   */
  view?: React.ReactNode;
  /**
   * Used in `renderItemView()` when `view` is not provided.
   */
  data?: TData;
  disabled?: boolean;
}

interface ListViewProps<TItemData = unknown> {
  list: Array<ListViewItem<TItemData>>;
  splitId: SplitViewProps["splitId"];
  splitMinSize?: SplitViewProps["minSize"];
  emptyListView?: React.ReactNode;
  onAdd?: ListPanelProps["onAdd"];
  actions?: ListPanelProps["actions"];
  disableSearch?: ListPanelProps["disableSearch"];
  multipleSearches?: ListPanelProps["multipleSearches"];
  renderItemView?: (item: { id: ListPanelItem["id"]; data?: TItemData }) => React.ReactNode;
}

function ListView<TItemData>({
  list,
  splitId,
  splitMinSize,
  emptyListView,
  onAdd,
  actions,
  disableSearch,
  multipleSearches,
  renderItemView,
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

  const renderView = () => {
    if (list.length === 0) {
      return emptyListView;
    }

    if (activeItem) {
      return activeItem.view || renderItemView?.({ id: activeItem.id, data: activeItem.data });
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
        disableSearch={disableSearch}
        multipleSearches={multipleSearches}
        renderItem={(item) => (
          <ListItemButton
            onClick={() => setActiveItem(item)}
            selected={activeItem?.id === item.id}
            disabled={item.disabled}
          >
            {renderListItem(item)}
          </ListItemButton>
        )}
      />
      <Box>{renderView()}</Box>
    </SplitView>
  );
}

export default ListView;
