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

import {
  Toolbar,
  alpha,
  Typography,
  Tooltip,
  IconButton,
  Fade,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { useTranslation } from "react-i18next";

interface Props {
  numSelected: number;
  handleDelete: () => void;
}

function TableToolbar({ numSelected, handleDelete }: Props) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Fade in={numSelected > 0} timeout={300}>
      <Toolbar
        sx={{
          ...(numSelected > 0 && {
            bgcolor: (theme) =>
              alpha(
                theme.palette.primary.main,
                theme.palette.action.activatedOpacity,
              ),
          }),
        }}
      >
        {numSelected > 0 && (
          <>
            <Typography sx={{ flex: 1 }}>
              {numSelected} {t("global.selected")}
            </Typography>
            <Tooltip title={t("global.delete")}>
              <IconButton onClick={handleDelete}>
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </>
        )}
      </Toolbar>
    </Fade>
  );
}

export default TableToolbar;
