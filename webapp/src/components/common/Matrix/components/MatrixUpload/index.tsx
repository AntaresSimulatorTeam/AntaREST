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
 * MatrixUpload.tsx - Main component that manages matrix uploads
 */
import { StudyMetadata } from "@/common/types";
import DatabaseUploadDialog from "@/components/common/dialogs/DatabaseUploadDialog";
import FileUploadDialog from "@/components/common/dialogs/FileUploadDialog";
import { useTranslation } from "react-i18next";

interface MatrixUploadProps {
  studyId: StudyMetadata["id"];
  path: string;
  type: "file" | "database";
  open: boolean;
  onClose: VoidFunction;
  onFileUpload?: (file: File) => Promise<void>;
  fileOptions?: {
    accept?: Record<string, string[]>;
    dropzoneText?: string;
  };
}

function MatrixUpload({
  studyId,
  path,
  type,
  open,
  onClose,
  onFileUpload,
  fileOptions,
}: MatrixUploadProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  // Import from the filesystem
  if (type === "file" && onFileUpload) {
    return (
      <FileUploadDialog
        open={open}
        title={t("matrix.importNewMatrix")}
        onCancel={onClose}
        onImport={onFileUpload}
        accept={fileOptions?.accept}
        dropzoneText={fileOptions?.dropzoneText}
      />
    );
  }

  // Import from the matrix store (database)
  if (type === "database") {
    return (
      <DatabaseUploadDialog
        studyId={studyId}
        path={path}
        open={open}
        onClose={onClose}
      />
    );
  }

  return null;
}

export default MatrixUpload;
