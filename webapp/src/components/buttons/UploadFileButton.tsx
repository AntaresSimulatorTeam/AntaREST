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
import { uploadFile } from "@/services/api/studies/raw";
import type { Study } from "@/services/api/studies/types";
import { createOrReplaceUserResource } from "@/services/api/studies/userResources";
import { toError } from "@/utils/fnUtils";
import FileUploadIcon from "@mui/icons-material/FileUpload";
import { Button } from "@mui/material";
import { useSnackbar } from "notistack";
import { useEffect, useState } from "react";
import { useDropzone, type Accept } from "react-dropzone";
import { useTranslation } from "react-i18next";

type ValidateResult = boolean | null | undefined;
type Validate = (file: File) => ValidateResult | Promise<ValidateResult>;

export interface UploadFileButtonProps {
  studyId: Study["id"];
  studyStorageMode: Study["storageMode"];
  path: string | ((file: File) => string);
  children?: React.ReactNode;
  accept?: Accept;
  disabled?: boolean;
  onUploadSuccessful?: (file: File) => void;
  validate?: Validate;
}

function UploadFileButton(props: UploadFileButtonProps) {
  const { t } = useTranslation();
  const {
    studyId,
    studyStorageMode,
    path,
    accept,
    disabled,
    onUploadSuccessful,
    children: label = t("global.import"),
  } = props;

  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { enqueueSnackbar } = useSnackbar();
  const [isUploading, setIsUploading] = useState(false);
  const { getInputProps, open } = useDropzone({
    onDropAccepted: handleDropAccepted,
    accept,
  });

  // Prevent the user from accidentally leaving the page while uploading
  useEffect(() => {
    if (isUploading) {
      const listener = (e: BeforeUnloadEvent) => {
        // eslint-disable-next-line no-param-reassign
        e.returnValue = t("global.import");
      };

      window.addEventListener("beforeunload", listener);

      return () => {
        window.removeEventListener("beforeunload", listener);
      };
    }
  }, [isUploading, t]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  async function handleDropAccepted(acceptedFiles: File[]) {
    setIsUploading(true);

    const fileToUpload = acceptedFiles[0];

    try {
      const isValid = (await props.validate?.(fileToUpload)) ?? true;

      if (!isValid) {
        return;
      }

      const filePath = typeof path === "function" ? path(fileToUpload) : path;

      if (studyStorageMode === "filesystem") {
        await uploadFile({
          studyId,
          path: filePath,
          file: fileToUpload,
          createMissing: true,
        });
      } else {
        await createOrReplaceUserResource({
          studyId,
          path: filePath,
          resourceType: "file",
          file: fileToUpload,
        });
      }

      enqueueSnackbar(t("global.import.success"), { variant: "success" });
    } catch (err) {
      enqueueErrorSnackbar(t("global.import.error"), toError(err));
      return;
    } finally {
      setIsUploading(false);
    }

    onUploadSuccessful?.(fileToUpload);
  }

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      {/* `open()` no working without the `<input>` in Firefox */}
      <input {...getInputProps()} />
      <Button
        variant="outlined"
        onClick={open}
        startIcon={<FileUploadIcon />}
        loadingPosition="start"
        loading={isUploading}
        disabled={disabled}
      >
        {label}
      </Button>
    </>
  );
}

export default UploadFileButton;
