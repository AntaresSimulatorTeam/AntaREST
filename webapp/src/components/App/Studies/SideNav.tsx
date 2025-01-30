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
import { Box, Typography, List, ListItem, ListItemText } from "@mui/material";
import { useTranslation } from "react-i18next";
import { STUDIES_SIDE_NAV_WIDTH } from "../../../theme";
import StudyTree from "@/components/App/Studies/StudyTree";
import useAppSelector from "../../../redux/hooks/useAppSelector";
import { getFavoriteStudies } from "../../../redux/selectors";

function SideNav() {
  const favorites = useAppSelector(getFavoriteStudies);
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <Box
      flex={`0 0 ${STUDIES_SIDE_NAV_WIDTH}px`}
      height="100%"
      display="flex"
      flexDirection="column"
      justifyContent="flex-start"
      alignItems="flex-start"
      boxSizing="border-box"
      p={2}
      sx={{ overflowX: "hidden", overflowY: "auto" }}
    >
      <Typography sx={{ color: "grey.400" }}>{t("studies.favorites")}</Typography>
      <List sx={{ width: "100%" }}>
        {favorites.map((fav) => (
          <ListItem
            key={fav.id}
            onClick={() => navigate(`/studies/${fav.id}`)}
            sx={{
              width: "100%",
              m: 0,
              py: 0,
              px: 1,
              cursor: "pointer",
              "&:hover": {
                bgcolor: "primary.outlinedHoverBackground",
              },
            }}
          >
            <ListItemText primary={fav.name} />
          </ListItem>
        ))}
      </List>
      <Typography sx={{ color: "grey.400" }}>Exploration</Typography>
      <StudyTree />
    </Box>
  );
}

export default SideNav;
