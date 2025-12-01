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

import { Box, Chip, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { LinkProperties } from "../../../../../../types/types";
import { setCurrentLayer, type StudyMapNode } from "../../../../../../redux/ducks/studyMaps";
import useAppDispatch from "../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../redux/hooks/useAppSelector";
import { getCurrentLayer, getStudyMapLayersById } from "../../../../../../redux/selectors";

interface Props {
  links: LinkProperties[];
  nodes: StudyMapNode[];
}

function MapHeader(props: Props) {
  const { nodes, links } = props;
  const dispatch = useAppDispatch();
  const [t] = useTranslation();
  const layers = useAppSelector(getStudyMapLayersById);
  const currentLayerId = useAppSelector(getCurrentLayer);

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleLayerClick = (layerId: string) => {
    dispatch(setCurrentLayer(layerId));
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        position: "absolute",
        padding: "10px",
        backdropFilter: "blur(2px)",
      }}
    >
      <Box
        sx={{
          display: "flex",
          width: "80%",
          flexWrap: "wrap",
        }}
      >
        {Object.values(layers).map(({ id, name }) => (
          <Chip
            key={id}
            label={name}
            color={currentLayerId === id ? "secondary" : "default"}
            clickable
            sx={{ m: 1 }}
            onClick={() => handleLayerClick(id)}
          />
        ))}
      </Box>
      <Box
        sx={{
          display: "flex",
        }}
      >
        <Typography sx={{ mx: 1 }}>{`${nodes.length} ${t("study.areas")}`}</Typography>
        <Typography sx={{ mx: 1 }}>{`${links.length} ${t("study.links")}`}</Typography>
      </Box>
    </Box>
  );
}

export default MapHeader;
