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

import { useNavigate } from "react-router";
import { Box, List, ListItemText, ListItemButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";
import StudyTree from "@/components/App/Studies/StudyTree";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getFavoriteStudies } from "@/redux/selectors";
import StarBorderIcon from "@mui/icons-material/StarBorder";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import FavoriteStudyToggle from "@/components/common/studies/FavoriteStudyToggle";
import ListCollapse from "@/components/common/ListCollapse";

function SideNav() {
  const favorites = useAppSelector(getFavoriteStudies);
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <Box sx={{ minWidth: 200, overflow: "auto" }}>
      {favorites.length > 0 && (
        <ListCollapse title={t("studies.favorites")} titleIcon={<StarBorderIcon />}>
          <List disablePadding dense>
            {favorites.map((fav) => (
              <ListItemButton
                key={fav.id}
                onClick={() => navigate(`/studies/${fav.id}`)}
                sx={{ pl: 4 }}
              >
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
        </ListCollapse>
      )}
      <ListCollapse title={t("studies.exploration")} titleIcon={<AccountTreeIcon />}>
        <StudyTree />
      </ListCollapse>
    </Box>
  );
}

export default SideNav;
