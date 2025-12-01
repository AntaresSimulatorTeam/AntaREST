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

import type { StudyMetadata } from "@/types/types";
import DatabaseUploadDialog from "@/components/common/dialogs/DatabaseUploadDialog";
import { useTranslation } from "react-i18next";
import UploadDialog from "../../dialogs/UploadDialog";

interface MatrixFileOptions {
  accept?: Record<string, string[]>;
  dropzoneText?: string;
}

interface BaseMatrixUploadProps {
  studyId: StudyMetadata["id"];
  path: string;
  open: boolean;
  onClose: VoidFunction;
}

interface FileMatrixUploadProps extends BaseMatrixUploadProps {
  type: "file";
  onFileUpload: (file: File) => Promise<void>;
  fileOptions?: MatrixFileOptions;
}

interface DatabaseMatrixUploadProps extends BaseMatrixUploadProps {
  type: "database";
  onFileUpload?: never;
  fileOptions?: never;
}

type MatrixUploadProps = FileMatrixUploadProps | DatabaseMatrixUploadProps;

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
      <UploadDialog
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
    return <DatabaseUploadDialog studyId={studyId} path={path} open={open} onClose={onClose} />;
  }

  return null;
}

export default MatrixUpload;
