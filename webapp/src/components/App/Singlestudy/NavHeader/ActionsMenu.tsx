/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useTranslation } from "react-i18next";

import { SvgIconComponent } from "@mui/icons-material";
import { ListItemIcon, ListItemText, Menu, MenuItem } from "@mui/material";

export interface ActionsMenuItem {
  key: string;
  icon: SvgIconComponent;
  action: VoidFunction | (() => Promise<void>);
  condition?: boolean;
  color?: string;
}

interface Props {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: VoidFunction;
  items: ActionsMenuItem[];
}

function ActionsMenu({ anchorEl, open, onClose, items }: Props) {
  const [t] = useTranslation();

  return (
    <Menu anchorEl={anchorEl} keepMounted open={open} onClose={onClose}>
      {items.map(
        (item) =>
          item.condition && (
            <MenuItem
              onClick={() => {
                item.action();
                onClose();
              }}
              key={item.key}
            >
              <ListItemIcon>
                <item.icon
                  sx={{
                    color: item.color,
                    width: "24px",
                    height: "24px",
                  }}
                />
              </ListItemIcon>
              <ListItemText sx={{ color: item.color }}>
                {t(item.key)}
              </ListItemText>
            </MenuItem>
          ),
      )}
    </Menu>
  );
}

export default ActionsMenu;
