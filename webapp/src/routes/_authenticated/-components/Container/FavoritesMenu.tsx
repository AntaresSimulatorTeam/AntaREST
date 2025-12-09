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

import useAppSelector from "@/redux/hooks/useAppSelector";
import { getFavoriteStudies } from "@/redux/selectors";
import FavoriteStudyToggle from "@/routes/-shared/components/studies/FavoriteStudyToggle";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import { List, ListItemButton, ListItemText, Tooltip } from "@mui/material";
import { useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import SidebarItem from "./SidebarItem";

function FavoritesMenu() {
  const { t } = useTranslation();
  const favorites = useAppSelector(getFavoriteStudies);
  const navigate = useNavigate();

  if (favorites.length === 0) {
    return null;
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <SidebarItem title={t("studies.favorites")} icon={<StarBorderIcon />}>
      <List disablePadding dense>
        {favorites.map((fav) => (
          <ListItemButton key={fav.id} onClick={() => navigate({ to: `/studies/${fav.id}` })}>
            <Tooltip title={fav.name}>
              <ListItemText
                primary={fav.name}
                slotProps={{
                  primary: {
                    sx: {
                      textWrap: "nowrap",
                      textOverflow: "ellipsis",
                      overflow: "hidden",
                    },
                  },
                }}
              />
            </Tooltip>
            <FavoriteStudyToggle studyId={fav.id} size="extra-small" />
          </ListItemButton>
        ))}
      </List>
    </SidebarItem>
  );
}

export default FavoritesMenu;
