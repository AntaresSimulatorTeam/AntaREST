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
  Tooltip,
} from "@mui/material";
import { Link, useLocation } from "@tanstack/react-router";
import { Children, useState } from "react";

type Props = {
  title: string;
  icon: React.ReactNode;
  onClick?: VoidFunction;
  link?: string;
  children?: React.ReactNode;
} & (
  | { link: string; children?: never; onClick?: never }
  | { children?: React.ReactNode; link?: never }
);

function SidebarItem({ title, icon, onClick, link, children }: Props) {
  const location = useLocation();
  const [expanded, setExpanded] = useState(false);
  const isMenuOpen = useAppSelector(isMainMenuOpen);
  const dispatch = useAppDispatch();
  const isCollapsible = Children.toArray(children).length > 0;
  const isExternalLink = link?.startsWith("http");
  const isSelected = link === location.pathname;

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const getButtonActionProps = () => {
    if (link) {
      return isExternalLink
        ? { href: link, target: "_blank", rel: "noopener noreferrer" }
        : { component: Link, to: link };
    }

    if (isCollapsible) {
      return {
        onClick: () => {
          if (isMenuOpen) {
            setExpanded(!expanded);
          } else {
            dispatch(setMainMenuOpen(true));
            setExpanded(true);
          }

          onClick?.();
        },
      };
    }

    return { onClick };
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={isMenuOpen ? "" : title} placement="right-end">
        <ListItem disablePadding>
          <ListItemButton
            sx={{ minHeight: 48, px: 2.5, justifyContent: isMenuOpen ? "initial" : "center" }}
            selected={isSelected}
            {...getButtonActionProps()}
          >
            <ListItemIcon
              sx={{ minWidth: 0, justifyContent: "center", mr: isMenuOpen ? 3 : "auto" }}
            >
              {icon}
            </ListItemIcon>
            <ListItemText primary={title} sx={{ opacity: isMenuOpen ? 1 : 0 }} />
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
          </ListItemButton>
        </ListItem>
      </Tooltip>
      {isMenuOpen && isCollapsible && <Collapse in={expanded}>{children}</Collapse>}
    </>
  );
}

export default SidebarItem;
