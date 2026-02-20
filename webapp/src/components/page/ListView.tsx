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
import { isSearchMatching } from "@/utils/stringUtils";
import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from "@mui/material";
import { Outlet, type ToOptions } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import SearchFE from "../fieldEditors/SearchFE";
import RouterListItemButton from "../router/RouterListItemButton";
import SplitView, { type SplitViewProps } from "./SplitView";

interface BaseListItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  loading?: boolean;
}

export interface RouteListItem extends BaseListItem {
  linkOptions: ToOptions;
  content?: never;
  data?: never;
}

export interface ContentListItem<TData = unknown> extends BaseListItem {
  linkOptions?: never;
  // It will be used in priority over `renderItemContent` if provided.
  content?: React.ReactNode;
  // Used in `renderItemContent` when `content` is not provided.
  data?: TData;
}

interface ListViewProps<TItemData = unknown> {
  list: RouteListItem[] | Array<ContentListItem<TItemData>>;
  splitId: SplitViewProps["splitId"];
  splitMinSize?: SplitViewProps["minSize"];
  emptyListContent?: React.ReactNode;
  onAdd?(): void;
  actions?: React.ReactNode;
  renderItemContent?: ({
    id,
    data,
  }: {
    id: BaseListItem["id"];
    data?: TItemData;
  }) => React.ReactNode;
}

function isRouteListItem(item: RouteListItem | ContentListItem): item is RouteListItem {
  return !!item?.linkOptions;
}

function isRouteList(list: RouteListItem[] | ContentListItem[]): list is RouteListItem[] {
  return list.length > 0 && isRouteListItem(list[0]);
}

function ListView<TItemData = unknown>({
  list,
  splitId,
  splitMinSize,
  emptyListContent,
  onAdd,
  actions,
  renderItemContent,
}: ListViewProps<TItemData>) {
  const [search, setSearch] = useState("");
  const { t } = useTranslation();
  const hasActions = !!onAdd || !!actions;
  const hasRouteList = isRouteList(list);
  const [activeContentItem, setActiveContentItem] = useState<
    ContentListItem<TItemData> | undefined
  >(() => (hasRouteList ? undefined : list[0]));
  // Get current route ID to force rebuilds of links when the route changes.
  // Allows to update relative links (e.g. `to: "."`).
  const currentRouteId = useCurrentRouteId();

  useEffect(() => {
    if (!hasRouteList) {
      setActiveContentItem(list[0]);
    }
  }, [list, hasRouteList]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const renderItemButton = (item: RouteListItem | ContentListItem<TItemData>) => {
    const buttonContent = (
      <>
        {item.icon && <ListItemIcon sx={{ minWidth: 0, pr: 1.5 }}>{item.icon}</ListItemIcon>}
        <ListItemText primary={item.label} slotProps={{ primary: { noWrap: true } }} />
      </>
    );

    if (isRouteListItem(item)) {
      return (
        <RouterListItemButton key={currentRouteId} {...item.linkOptions}>
          {buttonContent}
        </RouterListItemButton>
      );
    }

    return (
      <ListItemButton
        onClick={() => setActiveContentItem(item)}
        selected={activeContentItem?.id === item.id}
      >
        {buttonContent}
      </ListItemButton>
    );
  };

  const renderItemView = () => {
    if (list.length === 0) {
      return emptyListContent;
    }

    if (hasRouteList) {
      return <Outlet />;
    }

    if (activeContentItem) {
      return (
        activeContentItem.content ||
        renderItemContent?.({ id: activeContentItem.id, data: activeContentItem.data })
      );
    }

    return null;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SplitView splitId={splitId} minSize={splitMinSize}>
      <Box sx={{ display: "flex", flexDirection: "column" }}>
        {hasActions && (
          <Box
            sx={{
              display: "flex",
              gap: 1,
              p: 1,
              pb: 0,
            }}
          >
            {onAdd && (
              <Button startIcon={<AddIcon />} variant="contained" onClick={onAdd}>
                {t("global.add")}
              </Button>
            )}
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
        <List dense sx={{ overflow: "auto" }}>
          {list
            .filter((item) => isSearchMatching(search, item.label))
            .map((item) => (
              <Tooltip key={item.id} title={item.label} placement="right">
                <ListItem
                  disablePadding
                  secondaryAction={
                    item.loading && (
                      <CircularProgress
                        color="inherit"
                        size={16}
                        sx={{ verticalAlign: "middle" }}
                      />
                    )
                  }
                >
                  {renderItemButton(item)}
                </ListItem>
              </Tooltip>
            ))}
        </List>
      </Box>
      <Box>{renderItemView()}</Box>
    </SplitView>
  );
}

export default ListView;
