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

import RouterListItemButton, {
  type RouterListItemButtonProps,
} from "@/components/router/RouterListItemButton";
import RouterMenuItem, { type RouterMenuItemProps } from "@/components/router/RouterMenuItem";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryQueries } from "@/queries/directories/queries";
import { requestStudyFolderReveal, setStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getStudiesById, getStudyFilters, isMenuOpen } from "@/redux/selectors";
import FavoriteToggle from "@/routes/-shared/components/studies/FavoriteToggle";
import type { StudyMetadata } from "@/types/types";
import { getDescendantIds } from "@/utils/directoryUtils";
import { toError } from "@/utils/fnUtils";
import { getStudyFolder } from "@/utils/studiesUtils";
import FolderIcon from "@mui/icons-material/Folder";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import {
  IconButton,
  List,
  ListItemIcon,
  ListItemText,
  Menu,
  Tooltip,
  Typography,
} from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { linkOptions, useLocation, useNavigate } from "@tanstack/react-router";
import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import SidebarItem from "../SidebarItem";
import { type Favorite } from "./types";
import useFavorites from "./useFavorites";

function FavoritesMenu() {
  const { t } = useTranslation();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [revealingStudyId, setRevealingStudyId] = useState<string | null>(null);
  const revealRequestId = useRef(0);
  const isMainMenuOpen = useAppSelector(isMenuOpen);
  const studiesById = useAppSelector(getStudiesById);
  const {
    activeTree,
    managed: { directoryId },
    external: { path },
  } = useAppSelector(getStudyFilters);
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const favorites = useFavorites();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  useEffect(() => {
    setRevealingStudyId(null);

    // Ignore metadata that arrives after the user navigates somewhere else.
    return () => {
      revealRequestId.current += 1;
    };
  }, [location, activeTree, directoryId, path]);

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeMenu = () => {
    revealRequestId.current += 1;
    setRevealingStudyId(null);
    setAnchorEl(null);
  };

  const getFavoriteLinkOptions = (fav: Favorite) => {
    if (fav.type === "directory") {
      return {
        ...linkOptions({ to: "/studies" }),
        onClick: () => {
          dispatch(
            requestStudyFolderReveal({
              tree: "managed",
              directoryId: fav.original.directoryId,
              directoryIds: getDescendantIds(fav.original.directoryId, directories),
            }),
          );

          closeMenu();
        },
        activeProps: {},
      } satisfies RouterListItemButtonProps | RouterMenuItemProps;
    }

    if (fav.type === "externalDirectory") {
      return {
        ...linkOptions({ to: "/studies" }),
        onClick: () => {
          dispatch(
            requestStudyFolderReveal({
              tree: "external",
              path: fav.absolutePath,
            }),
          );

          closeMenu();
        },
        activeProps: {},
      } satisfies RouterListItemButtonProps | RouterMenuItemProps;
    }

    // Study favorite
    return {
      ...linkOptions({
        to: "/studies/$studyId",
        params: { studyId: fav.original.studyId },
      }),
      onClick: closeMenu,
    } satisfies RouterListItemButtonProps | RouterMenuItemProps;
  };

  const getFavoriteIcon = (fav: Favorite) => {
    if (fav.type === "directory") {
      return (
        <ListItemIcon sx={[isMainMenuOpen && { minWidth: 26 }]}>
          <FolderIcon fontSize="extra-small" color="info" />
        </ListItemIcon>
      );
    }

    if (fav.type === "externalDirectory") {
      return (
        <ListItemIcon sx={[isMainMenuOpen && { minWidth: 26 }]}>
          <FolderIcon fontSize="extra-small" sx={{ color: "text.secondary" }} />
        </ListItemIcon>
      );
    }

    return null;
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleShowInExplorer = async (
    event: React.MouseEvent<HTMLButtonElement>,
    studyId: string,
  ) => {
    event.preventDefault();
    event.stopPropagation();

    const requestId = ++revealRequestId.current;
    setRevealingStudyId(studyId);

    let study: StudyMetadata;

    try {
      study = studiesById[studyId] ?? (await dispatch(setStudy(studyId)).unwrap());
    } catch (error) {
      if (requestId === revealRequestId.current) {
        enqueueErrorSnackbar(t("studies.error.showInExplorer"), toError(error));
      }

      return;
    } finally {
      if (requestId === revealRequestId.current) {
        setRevealingStudyId(null);
      }
    }

    if (requestId !== revealRequestId.current) {
      return;
    }

    dispatch(requestStudyFolderReveal(getStudyFolder(study, directories)));
    setAnchorEl(null);

    // Selecting the folder invalidates the metadata token, so handle navigation errors separately.
    try {
      await navigate({ to: "/studies" });
    } catch (error) {
      enqueueErrorSnackbar(t("studies.error.showInExplorer"), toError(error));
    }
  };

  const handleItemClick = (event: React.MouseEvent<HTMLElement>) => {
    if (!isMainMenuOpen) {
      setAnchorEl(event.currentTarget);
    }
  };

  const handleFavoriteKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    const item = event.currentTarget;

    // MenuList moves between rows with arrows. Start from the row even when an
    // action button has focus, so it does not navigate between nested buttons.
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      if (event.target !== item) {
        item.focus();
      }

      return;
    }

    if (event.key !== "Tab") {
      return;
    }

    const controls = [item, ...item.querySelectorAll<HTMLButtonElement>("button:not(:disabled)")];
    const focusedIndex = controls.findIndex((control) => control === document.activeElement);
    const nextControl = controls[focusedIndex + (event.shiftKey ? -1 : 1)];

    // Give secondary actions a keyboard stop before Menu handles Tab by closing.
    if (nextControl) {
      event.preventDefault();
      event.stopPropagation();
      nextControl.focus();
    }
  };

  const getFavoriteContent = (fav: Favorite) => (
    <>
      {getFavoriteIcon(fav)}
      <Tooltip
        title={fav.name}
        placement="right"
        slotProps={{ popper: { modifiers: [{ name: "offset", options: { offset: [0, 30] } }] } }}
      >
        <ListItemText>
          <Typography noWrap variant="body2">
            {fav.name}
          </Typography>
        </ListItemText>
      </Tooltip>
      {fav.type === "study" && (
        <Tooltip title={t("studies.showInExplorer")} placement="right">
          <IconButton
            size="small"
            aria-label={t("studies.showInExplorer")}
            loading={revealingStudyId === fav.original.studyId}
            disabled={revealingStudyId !== null}
            onClick={(event) => handleShowInExplorer(event, fav.original.studyId)}
          >
            <FolderOpenIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
      <FavoriteToggle favorite={fav.original} edge="end" tooltipPlacement="right" />
    </>
  );

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
        {/* List - when main menu is expanded */}
        <List disablePadding dense>
          {favorites.map((fav) => (
            <RouterListItemButton key={fav.id} {...getFavoriteLinkOptions(fav)}>
              {getFavoriteContent(fav)}
            </RouterListItemButton>
          ))}
        </List>
      </SidebarItem>

      {/* Menu - when main menu is collapsed */}
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
            <RouterMenuItem
              key={fav.id}
              dense
              {...getFavoriteLinkOptions(fav)}
              onKeyDown={handleFavoriteKeyDown}
            >
              {getFavoriteContent(fav)}
            </RouterMenuItem>
          ))}
        </Menu>
      )}
    </>
  );
}

export default FavoritesMenu;
