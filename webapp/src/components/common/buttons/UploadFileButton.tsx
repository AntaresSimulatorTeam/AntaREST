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

import { LoadingButton } from "@mui/lab";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../utils/fnUtils";
import { useDropzone, type Accept } from "react-dropzone";
import type { StudyMetadata } from "../../../types/types";
import { useSnackbar } from "notistack";
import { uploadFile } from "../../../services/api/studies/raw";

type ValidateResult = boolean | null | undefined;
type Validate = (file: File) => ValidateResult | Promise<ValidateResult>;

export interface UploadFileButtonProps {
  studyId: StudyMetadata["id"];
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

      await uploadFile({
        studyId,
        path: filePath,
        file: fileToUpload,
        createMissing: true,
      });

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
      <LoadingButton
        variant="outlined"
        onClick={open}
        startIcon={<FileDownloadIcon />}
        loadingPosition="start"
        loading={isUploading}
        disabled={disabled}
      >
        {label}
      </LoadingButton>
    </>
  );
}

export default UploadFileButton;
