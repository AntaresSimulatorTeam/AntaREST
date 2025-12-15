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

import { isSearchMatching } from "@/utils/stringUtils";
import { Box, List, ListItem, Tooltip, Typography } from "@mui/material";
import { Outlet, type ToOptions } from "@tanstack/react-router";
import { useState } from "react";
import SearchFE from "../fieldEditors/SearchFE";
import RouterListItemButton from "../router/RouterListItemButton";
import SplitView from "./SplitView";

interface BaseItem {
  id: string;
  label: string;
}

interface RouteItem extends BaseItem {
  linkOptions: ToOptions;
}

interface ListViewProps<TItems extends RouteItem[] = RouteItem[]> {
  list: TItems;
  splitId: string;
  renderPanel?: (props: { children: React.ReactNode }, item: TItems[number]) => React.ReactNode;
  renderEmptyPanel?: () => React.ReactNode;
  actions?: React.ReactNode;
}

function ListView<TItems extends RouteItem[]>({
  list,
  splitId,
  renderPanel = ({ children }) => children,
  renderEmptyPanel,
  actions,
}: ListViewProps<TItems>) {
  const [search, setSearch] = useState("");

  return (
    <SplitView splitId={splitId}>
      <Box>
        {actions && (
          <Box
            sx={{
              display: "flex",
              gap: 1,
              p: 1,
              pb: 0,
            }}
          >
            {actions}
          </Box>
        )}
        {list.length > 0 && (
          <SearchFE
            value={search}
            onSearchValueChange={setSearch}
            size="extra-small"
            fullWidth
            sx={{ p: 1, pb: 0 }}
          />
        )}
        <List dense>
          {list
            .filter((item) => isSearchMatching(search, item.label))
            .map((item) => (
              <Tooltip key={item.id} title={item.label} placement="right">
                <ListItem disablePadding>
                  <RouterListItemButton {...item.linkOptions}>
                    <Typography noWrap>{item.label}</Typography>
                  </RouterListItemButton>
                </ListItem>
              </Tooltip>
            ))}
        </List>
      </Box>
      <Box>
        {list.length > 0
          ? renderPanel({ children: <Outlet /> }, {} as TItems[number])
          : renderEmptyPanel?.()}
      </Box>
    </SplitView>
  );
}

export default ListView;
