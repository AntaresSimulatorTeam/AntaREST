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

import LaunchIcon from "@mui/icons-material/Launch";
import { ListItem, ListItemButton, ListItemIcon, ListItemText, Tooltip } from "@mui/material";
import { Link, useLocation } from "react-router-dom";

interface Props {
  title: string;
  isMenuOpen: boolean;
  icon: React.ReactNode;
  onClick?: VoidFunction;
  link?: string;
}

function MenuItem({ title, isMenuOpen, icon, onClick, link }: Props) {
  const location = useLocation();
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
    return { onClick };
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Tooltip title={isMenuOpen ? "" : title} placement="right-end">
      <ListItem disablePadding>
        <ListItemButton
          sx={{ minHeight: 48, px: 2.5, justifyContent: isMenuOpen ? "initial" : "center" }}
          selected={isSelected}
          {...getButtonActionProps()}
        >
          <ListItemIcon sx={{ minWidth: 0, justifyContent: "center", mr: isMenuOpen ? 3 : "auto" }}>
            {icon}
          </ListItemIcon>
          <ListItemText primary={title} sx={{ opacity: isMenuOpen ? 1 : 0 }} />
          {isExternalLink && (
            <LaunchIcon
              fontSize="extra-small"
              sx={[{ opacity: 0.8 }, !isMenuOpen && { display: "none" }]}
            />
          )}
        </ListItemButton>
      </ListItem>
    </Tooltip>
  );
}

export default MenuItem;
