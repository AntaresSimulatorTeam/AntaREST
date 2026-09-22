/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
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

import RadarIcon from "@mui/icons-material/Radar";
import { useTranslation } from "react-i18next";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";

interface ScanDirectoryDialogProps {
  open: boolean;
  directoryPath: string;
  isRecursive: boolean;
  showRecursiveOption: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  onToggleRecursive: () => void;
}

function ScanDirectoryDialog({
  open,
  directoryPath,
  isRecursive,
  showRecursiveOption,
  onConfirm,
  onCancel,
  onToggleRecursive,
}: ScanDirectoryDialogProps) {
  const { t } = useTranslation();

  return (
    <ConfirmationDialog
      titleIcon={RadarIcon}
      onCancel={onCancel}
      onConfirm={onConfirm}
      alert="warning"
      open={open}
    >
      {t("studies.scanFolder")} {directoryPath}?
      {showRecursiveOption && (
        <CheckBoxFE
          label={t("studies.recursiveScan")}
          value={isRecursive}
          onChange={onToggleRecursive}
        />
      )}
    </ConfirmationDialog>
  );
}

export default ScanDirectoryDialog;
