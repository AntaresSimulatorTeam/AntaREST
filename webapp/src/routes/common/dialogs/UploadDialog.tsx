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

import { useEffect, useState } from "react";
import { Box, Button, LinearProgress, Paper, Typography, colors } from "@mui/material";
import { useDropzone, type Accept, type FileRejection } from "react-dropzone";
import { useTranslation } from "react-i18next";
import BasicDialog, { type BasicDialogProps } from "./BasicDialog";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../utils/fnUtils";
import { enqueueSnackbar } from "notistack";
import type { PromiseAny } from "../../../utils/tsUtils";
import FileUploadIcon from "@mui/icons-material/FileUpload";

export interface UploadDialogProps extends Omit<BasicDialogProps, "actions"> {
  dropzoneText?: string;
  accept?: Accept;
  onCancel: VoidFunction;
  onImport: (file: File, setUploadProgress: (progress: number) => void) => PromiseAny;
}

function UploadDialog(props: UploadDialogProps) {
  const { dropzoneText, accept, onImport, onCancel, onClose, title, ...dialogProps } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(-1);
  const [invalidText, setInvalidText] = useState("");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDropAccepted: handleDropAccepted,
    onDropRejected: handleDropRejected,
    disabled: isUploading,
    multiple: false,
    accept,
  });

  useEffect(() => {
    // Protect against data loss by preventing navigation/refresh during file upload
    // This displays a browser warning when trying to:
    // - Close the browser tab/window
    // - Refresh the page
    // - Navigate away from the page
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isUploading) {
        e.preventDefault();
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [isUploading]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  async function handleDropAccepted(acceptedFiles: File[]) {
    setInvalidText("");
    setIsUploading(true);

    const fileToUpload = acceptedFiles[0];

    try {
      await onImport(fileToUpload, setUploadProgress);

      enqueueSnackbar(t("common.dialog.import.importSuccess"), {
        variant: "success",
      });
      onCancel();
    } catch (err) {
      enqueueErrorSnackbar(t("common.dialog.import.importError"), toError(err));
    }

    setIsUploading(false);
    setUploadProgress(-1);
  }

  function handleDropRejected(fileRejections: FileRejection[]) {
    setInvalidText(fileRejections[0].errors[0].message);
  }

  const handleClose: UploadDialogProps["onClose"] = (...args) => {
    if (!isUploading) {
      onCancel();
      onClose?.(...args);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <BasicDialog
      {...dialogProps}
      title={title || t("global.import")}
      titleIcon={FileUploadIcon}
      actions={
        <Button onClick={onCancel} disabled={isUploading}>
          {t("global.close")}
        </Button>
      }
      onClose={handleClose}
    >
      <Box sx={{ pt: 1 }}>
        {isUploading ? (
          <LinearProgress
            variant={uploadProgress > 2 && uploadProgress < 98 ? "determinate" : "indeterminate"}
            value={Math.max(0, Math.min(100, uploadProgress))}
          />
        ) : (
          <>
            <Paper
              {...getRootProps()}
              elevation={0}
              sx={{
                borderWidth: 1,
                borderStyle: "dashed",
                borderColor: isDragActive ? colors.blue[500] : colors.grey[500],
                transition: "border .24s ease-in-out",
                p: 4,
                cursor: "pointer",
                position: "relative",
                background: "none",
              }}
            >
              <input {...getInputProps()} />
              <Typography sx={{ textAlign: "center" }}>
                {dropzoneText || t("common.dialog.import.dropzoneText")}
              </Typography>
            </Paper>
            {invalidText && (
              <Typography
                sx={{
                  textAlign: "center",
                  color: "error.main",
                  pt: 1,
                }}
              >
                {invalidText}
              </Typography>
            )}
          </>
        )}
      </Box>
    </BasicDialog>
  );
}

export default UploadDialog;
