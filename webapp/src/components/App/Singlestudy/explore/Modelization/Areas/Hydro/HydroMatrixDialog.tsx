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

import { Button, Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, {
  BasicDialogProps,
} from "../../../../../../common/dialogs/BasicDialog";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

interface Props {
  open: boolean;
  onClose: () => void;
  type: HydroMatrixType;
}

function HydroMatrixDialog({ open, onClose, type }: Props) {
  const { t } = useTranslation();
  const dialogProps: BasicDialogProps = {
    open,
    onClose,
    actions: (
      <Button onClick={onClose} color="primary" variant="outlined">
        {t("global.close")}
      </Button>
    ),
  };

  return (
    <BasicDialog
      {...dialogProps}
      contentProps={{
        sx: { p: 0, height: "90vh" },
      }}
      fullWidth
      maxWidth="xl"
    >
      <Box sx={{ width: 1, height: 1, p: 2 }}>
        <HydroMatrix type={type} />
      </Box>
    </BasicDialog>
  );
}

export default HydroMatrixDialog;
