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

import useCurrentRouteId from "@/hooks/router/useCurrentRouteId";
import { Box } from "@mui/material";
import { Outlet, type ToOptions } from "@tanstack/react-router";
import ListPanel, { type ListPanelItem } from "../../ListPanel";
import RouterListItemButton from "../../router/RouterListItemButton";
import SplitView, { type SplitViewProps } from "../SplitView";
import { renderListItem } from "./utils";

export interface RouterListViewItem extends ListPanelItem {
  linkOptions: ToOptions;
}

interface RouterListViewProps {
  list: RouterListViewItem[];
  splitId: SplitViewProps["splitId"];
  splitMinSize?: SplitViewProps["minSize"];
  emptyListView?: React.ReactNode;
  onAdd?(): void;
  actions?: React.ReactNode;
}

function RouterListView({
  list,
  splitId,
  splitMinSize,
  emptyListView,
  onAdd,
  actions,
}: RouterListViewProps) {
  // Get current route ID to force rebuilds of links when the route changes.
  // Allows to update relative links (e.g. `to: "."`).
  const currentRouteId = useCurrentRouteId();

  return (
    <SplitView splitId={splitId} minSize={splitMinSize}>
      <ListPanel
        list={list}
        onAdd={onAdd}
        actions={actions}
        renderItemContent={(item) => (
          <RouterListItemButton key={currentRouteId} {...item.linkOptions}>
            {renderListItem(item)}
          </RouterListItemButton>
        )}
      />
      <Box>{list.length > 0 ? <Outlet /> : emptyListView}</Box>
    </SplitView>
  );
}

export default RouterListView;
