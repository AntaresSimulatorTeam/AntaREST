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

import RouterListItemButton from "@/components/router/RouterListItemButton";
import RouterMenuItem from "@/components/router/RouterMenuItem";
import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isMenuOpen } from "@/redux/selectors";
import FavoriteToggle from "@/routes/-shared/components/studies/FavoriteToggle.tsx";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { List, ListItemText, Menu, Tooltip, Typography } from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { linkOptions } from "@tanstack/react-router";
import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { getDescendantIds } from "../../../studies/-components/StudyTree/ManagedTree/utils";
import SidebarItem from "../SidebarItem";
import useFavorites from "./useFavorites";
import { getTooltipProps, type Favorite } from "./utils";

function FavoritesMenu() {
  const { t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const isMainMenuOpen = useAppSelector(isMenuOpen);
  const dispatch = useDispatch();
  const favorites = useFavorites();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeMenu = () => {
    setAnchorEl(null);
  };

  const getFavoriteItemLinkOptions = (fav: Favorite) => {
    // Study favorite
    if (fav.type === "study") {
      return {
        ...linkOptions({
          to: "/studies/$studyId",
          params: { studyId: fav.id },
        }),
        onClick: closeMenu,
      };
    }

    // Directory favorite
    return {
      ...linkOptions({ to: "/studies" }),
      onClick: () => {
        dispatch(
          updateStudyFilters({
            activeTree: "managed",
            managed: {
              directoryId: fav.id,
              directoryIds: getDescendantIds(fav.id, directories),
            },
          }),
        );

        closeMenu();
      },
    };
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleItemClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (!isMainMenuOpen) {
      setAnchorEl(event.currentTarget);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  if (favorites.length === 0) {
    return null;
  }

  return (
    <>
      <SidebarItem
        label={t("studies.favorites")}
        icon={<StarBorderIcon />}
        onClick={handleItemClick}
        disableAutoMainMenuOpen
      >
        {/* List - when main menu is open */}
        <List disablePadding dense>
          {favorites.map((fav) => (
            <RouterListItemButton key={fav.id} {...getFavoriteItemLinkOptions(fav)}>
              <Tooltip {...getTooltipProps(fav, [0, 30])}>
                <ListItemText>
                  <Typography noWrap variant="body2">
                    {fav.name}
                  </Typography>
                </ListItemText>
              </Tooltip>
              <FavoriteToggle favorite={fav.original} edge="end" tooltipPlacement="right" />
            </RouterListItemButton>
          ))}
        </List>
      </SidebarItem>

      {/* Menu - when main menu is closed */}
      {!isMainMenuOpen && (
        <Menu
          open={!!anchorEl}
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: "top",
            horizontal: "right",
          }}
          sx={{ maxWidth: 500 }}
          onClose={closeMenu}
        >
          {favorites.map((fav) => (
            <RouterMenuItem key={fav.id} dense {...getFavoriteItemLinkOptions(fav)}>
              <Tooltip {...getTooltipProps(fav, [0, 30])}>
                <ListItemText>
                  <Typography noWrap variant="body2" sx={{ mr: 1 }}>
                    {fav.name}
                  </Typography>
                </ListItemText>
              </Tooltip>
              <FavoriteToggle favorite={fav.original} edge="end" tooltipPlacement="right" />
            </RouterMenuItem>
          ))}
        </Menu>
      )}
    </>
  );
}

export default FavoritesMenu;
