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

import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { toError } from "@/utils/fnUtils";
import type { PromiseAny } from "@/utils/tsUtils";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import { Box, Button, LinearProgress, Paper, Typography, colors } from "@mui/material";
import { enqueueSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useDropzone, type Accept, type FileRejection } from "react-dropzone";
import { useTranslation } from "react-i18next";
import BasicDialog, { type BasicDialogProps } from "./BasicDialog";

export interface UploadImportResult {
  success: number;
  failed: number;
  total: number;
}

export interface UploadDialogProps extends Omit<BasicDialogProps, "actions"> {
  dropzoneText?: string;
  accept?: Accept;
  /** Allow selecting/dropping several files at once. Each file is imported independently via `onImport`. */
  multiple?: boolean;
  onCancel: VoidFunction;
  onImport: (file: File, setUploadProgress: (progress: number) => void) => PromiseAny;
  /** Called once after all selected files have been processed (a single file counts as a batch of 1). */
  onImportComplete?: (result: UploadImportResult) => PromiseAny;
  /** Optional content rendered above the dropzone (e.g. extra form fields). */
  extraContent?: React.ReactNode;
}

function UploadDialog(props: UploadDialogProps) {
  const {
    dropzoneText,
    accept,
    multiple,
    onImport,
    onImportComplete,
    onCancel,
    onClose,
    title,
    extraContent,
    ...dialogProps
  } = props;
  const [t] = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(-1);
  const [uploadStatusText, setUploadStatusText] = useState("");
  const [invalidText, setInvalidText] = useState("");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDropAccepted: handleDropAccepted,
    onDropRejected: handleDropRejected,
    disabled: isUploading,
    multiple: multiple ?? false,
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

    if (acceptedFiles.length > 1) {
      await importFiles(acceptedFiles);
    } else {
      await importSingleFile(acceptedFiles[0]);
    }

    setIsUploading(false);
    setUploadProgress(-1);
    setUploadStatusText("");
  }

  async function importSingleFile(file: File) {
    try {
      await onImport(file, setUploadProgress);

      enqueueSnackbar(t("common.dialog.import.importSuccess"), {
        variant: "success",
      });
      await onImportComplete?.({ success: 1, failed: 0, total: 1 });
      onCancel();
    } catch (err) {
      enqueueErrorSnackbar(t("common.dialog.import.importError"), toError(err));
    }
  }

  async function importFiles(files: File[]) {
    let success = 0;
    let failed = 0;

    for (const [index, file] of files.entries()) {
      setUploadStatusText(
        t("common.dialog.import.importingFile", {
          current: index + 1,
          total: files.length,
          name: file.name,
        }),
      );

      try {
        await onImport(file, (fileProgress) => {
          setUploadProgress(((index + fileProgress / 100) / files.length) * 100);
        });
        success += 1;
      } catch (err) {
        failed += 1;
        enqueueErrorSnackbar(
          t("common.dialog.import.importErrorFile", { name: file.name }),
          toError(err),
        );
      }
    }

    enqueueSnackbar(
      t("common.dialog.import.importSummary", { success, failed, total: files.length }),
      { variant: failed === 0 ? "success" : success === 0 ? "error" : "warning" },
    );

    if (success > 0) {
      await onImportComplete?.({ success, failed, total: files.length });
    }

    onCancel();
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
      <Box
        sx={{
          pt: 1,
          display: "flex",
          flexDirection: "column",
          gap: 2,
          // When extra content is provided, fill the available dialog content height
          // so consumers can use a tall dialog without leaving empty space below.
          ...(extraContent && { flex: 1, minHeight: 0 }),
        }}
      >
        {extraContent}
        {isUploading ? (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
            {uploadStatusText && (
              <Typography variant="body2" sx={{ textAlign: "center", color: "text.secondary" }}>
                {uploadStatusText}
              </Typography>
            )}
            <LinearProgress
              variant={uploadProgress > 2 && uploadProgress < 98 ? "determinate" : "indeterminate"}
              value={Math.max(0, Math.min(100, uploadProgress))}
            />
          </Box>
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
