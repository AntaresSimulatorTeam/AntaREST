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
import AddIcon from "@mui/icons-material/Add";
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Tooltip,
} from "@mui/material";
import { Outlet, type ToOptions } from "@tanstack/react-router";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import SearchFE from "../fieldEditors/SearchFE";
import RouterListItemButton from "../router/RouterListItemButton";
import SplitView from "./SplitView";

interface BaseListItem {
  id: string;
  label: string;
  loading?: boolean;
}

export interface RouteListItem extends BaseListItem {
  linkOptions: ToOptions;
}

interface ListViewProps {
  list: RouteListItem[];
  splitId: string;
  emptyListContent?: React.ReactNode;
  onAdd?(): void;
  actions?: React.ReactNode;
}

function ListView({ list, splitId, emptyListContent, onAdd, actions }: ListViewProps) {
  const [search, setSearch] = useState("");
  const { t } = useTranslation();
  const hasActions = !!onAdd || !!actions;

  return (
    <SplitView splitId={splitId}>
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
                  secondaryAction={item.loading && <CircularProgress color="inherit" size={16} />}
                >
                  <RouterListItemButton {...item.linkOptions}>
                    <ListItemText primary={item.label} slotProps={{ primary: { noWrap: true } }} />
                  </RouterListItemButton>
                </ListItem>
              </Tooltip>
            ))}
        </List>
      </Box>
      <Box>{list.length > 0 ? <Outlet /> : emptyListContent}</Box>
    </SplitView>
  );
}

export default ListView;
