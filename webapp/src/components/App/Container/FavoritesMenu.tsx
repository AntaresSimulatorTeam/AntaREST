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

import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import {
  Collapse,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import FavoriteStudyToggle from "@/components/App/shared/studies/FavoriteStudyToggle";
import { getFavoriteStudies } from "@/redux/selectors";
import { setMenuOpen } from "@/redux/ducks/ui";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import useAppDispatch from "@/redux/hooks/useAppDispatch";

interface FavoritesMenuProps {
  isMenuOpen: boolean;
}

function FavoritesMenu({ isMenuOpen }: FavoritesMenuProps) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const favorites = useAppSelector(getFavoriteStudies);
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(false);

  if (favorites.length === 0) {
    return null;
  }

  const handleToggle = () => {
    if (isMenuOpen) {
      setExpanded(!expanded);
    } else {
      dispatch(setMenuOpen(true));
      setExpanded(true);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Tooltip title={isMenuOpen ? "" : t("studies.favorites")} placement="right-end">
        <ListItem disablePadding>
          <ListItemButton
            sx={{ minHeight: 48, px: 2.5, justifyContent: isMenuOpen ? "initial" : "center" }}
            onClick={handleToggle}
          >
            <ListItemIcon
              sx={{ minWidth: 0, justifyContent: "center", mr: isMenuOpen ? 3 : "auto" }}
            >
              <StarBorderIcon />
            </ListItemIcon>
            <ListItemText primary={t("studies.favorites")} sx={{ opacity: isMenuOpen ? 1 : 0 }} />
            {isMenuOpen && (
              <ListItemIcon sx={{ minWidth: 0, justifyContent: "center" }}>
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItemIcon>
            )}
          </ListItemButton>
        </ListItem>
      </Tooltip>
      {isMenuOpen && (
        <Collapse in={expanded}>
          <List disablePadding dense>
            {favorites.map((fav) => (
              <ListItemButton key={fav.id} onClick={() => navigate(`/studies/${fav.id}`)}>
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
        </Collapse>
      )}
    </>
  );
}

export default FavoritesMenu;
