/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import SettingsIcon from "@mui/icons-material/Settings";
import AddIcon from "@mui/icons-material/Add";
import RemoveIcon from "@mui/icons-material/Remove";
import { Box } from "@mui/material";
import { MAX_ZOOM_LEVEL, MIN_ZOOM_LEVEL } from "./utils";

interface Props {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onOpenConfig: () => void;
  zoomLevel: number;
}

function MapControlButtons({
  onZoomIn,
  onZoomOut,
  onOpenConfig,
  zoomLevel,
}: Props) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        position: "absolute",
        bottom: 15,
        right: 15,
      }}
    >
      <ButtonGroup
        color="primary"
        orientation="vertical"
        variant="outlined"
        size="small"
        sx={{ mb: 2 }}
      >
        <Button onClick={onZoomIn} disabled={zoomLevel >= MAX_ZOOM_LEVEL}>
          <AddIcon />
        </Button>
        <Button onClick={onZoomOut} disabled={zoomLevel <= MIN_ZOOM_LEVEL}>
          <RemoveIcon />
        </Button>
      </ButtonGroup>
      <Button
        onClick={onOpenConfig}
        variant="outlined"
        size="small"
        color="primary"
        sx={{ minWidth: 40 }}
      >
        <SettingsIcon />
      </Button>
    </Box>
  );
}

export default MapControlButtons;
