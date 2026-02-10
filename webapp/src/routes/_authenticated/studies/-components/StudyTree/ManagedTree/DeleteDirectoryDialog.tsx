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

import {
  Button,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
  Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import BasicDialog, { type BasicDialogProps } from "@/components/dialogs/BasicDialog";

export interface DeleteDirectoryDialogProps extends Omit<BasicDialogProps, "actions"> {
  directoryName: string;
  hasChildren: boolean;
  onConfirm: (cascade: boolean) => void;
  onCancel: VoidFunction;
}

function DeleteDirectoryDialog({
  directoryName,
  hasChildren,
  onConfirm,
  onCancel,
  onClose,
  ...basicDialogProps
}: DeleteDirectoryDialogProps) {
  const { t } = useTranslation();
  const [cascade, setCascade] = useState(true);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleClose = (...args: Parameters<NonNullable<BasicDialogProps["onClose"]>>) => {
    onCancel();
    onClose?.(...args);
  };

  const handleConfirm = () => {
    onConfirm(cascade);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      title={t("studies.deleteDirectory.title")}
      onClose={handleClose}
      alert="error"
      maxWidth="sm"
      fullWidth
      {...basicDialogProps}
      actions={
        <>
          <Button onClick={onCancel} color="inherit">
            {t("global.cancel")}
          </Button>
          <Button onClick={handleConfirm} variant="contained" color="error">
            {t("global.delete")}
          </Button>
        </>
      }
    >
      <Typography variant="body2" sx={{ mb: 2 }}>
        {hasChildren
          ? t("studies.deleteFolder.messageWithChildren", {
              directoryName,
            })
          : t("studies.deleteFolder.messageNoChildren", {
              directoryName,
            })}
      </Typography>

      {hasChildren && (
        <FormControl component="fieldset" sx={{ mt: 2 }}>
          <RadioGroup value={cascade} onChange={(e) => setCascade(e.target.value === "true")}>
            <FormControlLabel
              value={true}
              control={<Radio />}
              label={
                <Typography variant="body2">{t("studies.deleteFolder.cascadeOption")}</Typography>
              }
            />
            <FormControlLabel
              value={false}
              control={<Radio />}
              label={
                <Typography variant="body2">
                  {t("studies.deleteFolder.folderOnlyOption")}
                </Typography>
              }
            />
          </RadioGroup>
        </FormControl>
      )}
    </BasicDialog>
  );
}

export default DeleteDirectoryDialog;
