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

import { useTranslation } from "react-i18next";
import type { MatrixInfoDTO } from "../../../types/types";
import BasicDialog from "@/components/common/dialogs/BasicDialog";
import MatrixContent from "@/components/common/dialogs/DatabaseUploadDialog/components/MatrixContent";
import { Button } from "@mui/material";

interface PropTypes {
  matrix: MatrixInfoDTO;
  open: boolean;
  onClose: () => void;
}

function MatrixDialog({ matrix, open, onClose }: PropTypes) {
  const [t] = useTranslation();

  return (
    <BasicDialog
      title={t("global.import.fromDatabase")}
      open={open}
      onClose={onClose}
      actions={<Button onClick={onClose}>{t("global.close")}</Button>}
      maxWidth="xl"
      fullWidth
      contentProps={{
        sx: { p: 1, height: "95vh", width: 1 },
      }}
    >
      <MatrixContent matrix={matrix} onBack={onClose} />
    </BasicDialog>
  );
}

export default MatrixDialog;
