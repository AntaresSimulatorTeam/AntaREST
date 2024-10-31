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

import { useEffect, useState } from "react";
import { Box, Button, LinearProgress, Paper, Typography } from "@mui/material";
import { FileRejection, useDropzone, type Accept } from "react-dropzone";
import { useTranslation } from "react-i18next";
import BasicDialog, { BasicDialogProps } from "./BasicDialog";
import { blue, grey } from "@mui/material/colors";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import { enqueueSnackbar } from "notistack";
import { PromiseAny } from "@/utils/tsUtils";
import FileDownloadIcon from "@mui/icons-material/FileDownload";

interface ImportDialogProps extends Omit<BasicDialogProps, "actions"> {
  dropzoneText?: string;
  accept?: Accept;
  onCancel: VoidFunction;
  onImport: (
    file: File,
    setUploadProgress: (progress: number) => void,
  ) => PromiseAny;
}

function ImportDialog(props: ImportDialogProps) {
  const {
    dropzoneText,
    accept,
    onImport,
    onCancel,
    onClose,
    title,
    ...dialogProps
  } = props;
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
    if (isUploading) {
      const listener = (e: BeforeUnloadEvent) => {
        // eslint-disable-next-line no-param-reassign
        e.returnValue = "Import";
      };

      window.addEventListener("beforeunload", listener);

      return () => {
        window.removeEventListener("beforeunload", listener);
      };
    }
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

  const handleClose: ImportDialogProps["onClose"] = (...args) => {
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
      titleIcon={FileDownloadIcon}
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
            variant={
              uploadProgress > 2 && uploadProgress < 98
                ? "determinate"
                : "indeterminate"
            }
            value={Math.max(0, Math.min(100, uploadProgress))}
          />
        ) : (
          <>
            <Paper
              {...getRootProps()}
              sx={{
                borderWidth: 1,
                borderStyle: "dashed",
                borderColor: isDragActive ? blue[500] : grey[500],
                transition: "border .24s ease-in-out",
                p: 4,
                backgroundColor: "#262733",
                color: grey[400],
                cursor: "pointer",
                position: "relative",
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

export default ImportDialog;
