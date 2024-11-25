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

/**
 * FileUploadDialog.tsx - Handles file-based matrix uploads
 */
import { Box, Typography, Button, LinearProgress } from "@mui/material";
import { FileDownload } from "@mui/icons-material";

import { useTranslation } from "react-i18next";
import { useDropzone, DropzoneOptions, FileRejection } from "react-dropzone";
import { styled } from "@mui/material/styles";
import BasicDialog from "@/components/common/dialogs/BasicDialog";
import { PromiseAny } from "@/utils/tsUtils";
import { grey, blue } from "@mui/material/colors";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import { enqueueSnackbar } from "notistack";
import { useState } from "react";

interface FileUploadDialogProps {
  open: boolean;
  title: string;
  onCancel: VoidFunction;
  onImport: (file: File) => PromiseAny;
  accept?: DropzoneOptions["accept"];
  dropzoneText?: string;
}

const DropZoneArea = styled(Box)(({ theme }) => ({
  borderWidth: 1,
  borderStyle: "dashed",
  borderColor: grey[500],
  transition: "border .24s ease-in-out",
  padding: theme.spacing(4),
  backgroundColor: "#262733",
  color: grey[400],
  cursor: "pointer",
  position: "relative",
  "&:hover": {
    borderColor: blue[500],
  },
}));

function FileUploadDialog({
  open,
  title,
  onCancel,
  onImport,
  accept,
  dropzoneText,
}: FileUploadDialogProps) {
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isUploading, setIsUploading] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDropAccepted = async (file: File) => {
    setIsUploading(true);

    try {
      await onImport(file);

      enqueueSnackbar(t("common.dialog.import.importSuccess"), {
        variant: "success",
      });

      onCancel();
    } catch (err) {
      enqueueErrorSnackbar(t("common.dialog.import.importError"), toError(err));
    } finally {
      setIsUploading(false);
    }
  };

  const handleDropRejected = (fileRejections: FileRejection[]) => {
    setIsUploading(false);
    const err = fileRejections[0].errors[0].message;
    enqueueErrorSnackbar(t("common.dialog.import.importError"), toError(err));
  };

  const handleClose = () => {
    if (!isUploading) {
      onCancel();
    }
  };

  ////////////////////////////////////////////////////////////////
  // Hooks
  ////////////////////////////////////////////////////////////////

  const { getRootProps, getInputProps } = useDropzone({
    onDropAccepted: ([file]) => handleDropAccepted(file),
    onDropRejected: handleDropRejected,
    disabled: isUploading,
    multiple: false,
    accept,
    maxFiles: 1,
  });

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      open={open}
      title={title || t("matrix.importNewMatrix")}
      titleIcon={FileDownload}
      actions={
        <Button onClick={onCancel} disabled={isUploading}>
          {t("global.close")}
        </Button>
      }
      onClose={handleClose}
      fullWidth
      maxWidth="sm"
    >
      <Box sx={{ pt: 1 }}>
        {isUploading ? (
          <LinearProgress />
        ) : (
          <>
            <DropZoneArea {...getRootProps()}>
              <input {...getInputProps()} />
              <Typography sx={{ textAlign: "center" }}>
                {dropzoneText || t("common.dialog.import.dropzoneText")}
              </Typography>
            </DropZoneArea>
          </>
        )}
      </Box>
    </BasicDialog>
  );
}

export default FileUploadDialog;
