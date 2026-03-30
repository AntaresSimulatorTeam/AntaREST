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
import { setMenuOpen as setMainMenuOpen } from "@/redux/ducks/ui";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { isMenuOpen as isMainMenuOpen } from "@/redux/selectors";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import LaunchIcon from "@mui/icons-material/Launch";
import {
  Collapse,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Tooltip,
} from "@mui/material";
import { type ToOptions } from "@tanstack/react-router";
import type { TFunction } from "i18next";
import { Children, useState } from "react";
import { useTranslation } from "react-i18next";

interface BaseProps {
  label: string | ((t: TFunction) => string);
  icon: React.ReactNode;
}

interface LinkItemProps extends BaseProps {
  linkOptions: ToOptions | { href: string };
  disableAutoActive?: boolean;
  disableAutoMainMenuOpen?: never;
  children?: never;
  onClick?: never;
}

interface CollapsibleItemProps extends BaseProps {
  linkOptions?: never;
  disableAutoActive?: never;
  disableAutoMainMenuOpen?: boolean;
  children?: React.ReactNode;
  onClick?: React.MouseEventHandler<HTMLAnchorElement>;
}

export type SidebarItemProps = LinkItemProps | CollapsibleItemProps;

function SidebarItem({
  label,
  icon,
  onClick,
  linkOptions,
  disableAutoActive,
  disableAutoMainMenuOpen,
  children,
}: SidebarItemProps) {
  const [expanded, setExpanded] = useState(false);
  const isMenuOpen = useAppSelector(isMainMenuOpen);
  const dispatch = useAppDispatch();
  const { t } = useTranslation();
  const isCollapsible = Children.toArray(children).length > 0;
  const isExternalLink = !!linkOptions && "href" in linkOptions;
  const isRouterLink = !!linkOptions && !isExternalLink;
  const labelText = typeof label === "function" ? label(t) : label;

  const listItemBtnSx = {
    minHeight: 48,
    px: 2.5,
    justifyContent: isMenuOpen ? "initial" : "center",
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
    if (isCollapsible) {
      if (isMenuOpen) {
        setExpanded(!expanded);
      } else if (!disableAutoMainMenuOpen) {
        dispatch(setMainMenuOpen(true));
        setExpanded(true);
      }
    }

    onClick?.(event);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const buttonContent = (
    <>
      <ListItemIcon sx={{ minWidth: 0, justifyContent: "center", mr: isMenuOpen ? 3 : "auto" }}>
        {icon}
      </ListItemIcon>
      <ListItemText primary={labelText} sx={{ opacity: isMenuOpen ? 1 : 0 }} />
      {isExternalLink && (
        <LaunchIcon
          fontSize="extra-small"
          sx={[{ opacity: 0.8 }, !isMenuOpen && { display: "none" }]}
        />
      )}
      {isMenuOpen && isCollapsible && (
        <ListItemIcon sx={{ minWidth: 0, justifyContent: "center" }}>
          {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
        </ListItemIcon>
      )}
    </>
  );

  return (
    <>
      <Tooltip title={isMenuOpen ? "" : labelText} placement="right">
        <ListItem disablePadding>
          {isRouterLink ? (
            <RouterListItemButton
              {...linkOptions}
              activeProps={disableAutoActive ? undefined : { selected: true }}
              sx={listItemBtnSx}
            >
              {buttonContent}
            </RouterListItemButton>
          ) : (
            <ListItemButton
              href={linkOptions ? linkOptions.href : ""}
              target="_blank"
              rel="noopener noreferrer"
              onClick={handleClick}
              sx={listItemBtnSx}
            >
              {buttonContent}
            </ListItemButton>
          )}
        </ListItem>
      </Tooltip>
      {isMenuOpen && isCollapsible && (
        <Collapse in={expanded}>
          <Paper
            sx={{
              boxShadow: "inset 0px 1px 4px rgba(0,0,0,0.15)",
              borderRadius: 0,
            }}
          >
            {children}
          </Paper>
        </Collapse>
      )}
    </>
  );
}

export default SidebarItem;
