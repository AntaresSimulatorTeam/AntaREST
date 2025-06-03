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

import { Box, Button } from "@mui/material";
import * as RA from "ramda-adjunct";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import MatrixDialog from "../../../../../Data/MatrixDialog";
import { CommandEnum, type CommandItem } from "../../commandTypes";

interface PropTypes {
  command: CommandItem;
}

function CommandMatrixViewer(props: PropTypes) {
  const { command } = props;
  const { action, args } = command;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const matrixId = (args as any).matrix;
  const [openViewer, setOpenViewer] = useState(false);
  const [t] = useTranslation();

  if (action === CommandEnum.REPLACE_MATRIX && RA.isString(matrixId)) {
    return (
      <Box sx={{ mt: 1 }}>
        <Button
          variant="text"
          onClick={() => {
            setOpenViewer((prev) => !prev);
          }}
        >
          {t("data.viewMatrix")}
        </Button>
        <MatrixDialog
          matrix={{ id: matrixId, name: matrixId }}
          open={openViewer}
          onClose={() => {
            setOpenViewer(false);
          }}
        />
      </Box>
    );
  }
  return <div />;
}

export default CommandMatrixViewer;
