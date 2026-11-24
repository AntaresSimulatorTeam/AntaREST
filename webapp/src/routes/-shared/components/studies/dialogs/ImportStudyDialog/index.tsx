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

import { Divider, Typography } from "@mui/material";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import UploadDialog, { type UploadDialogProps } from "@/components/dialogs/UploadDialog";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";
import SelectFE, { type Options } from "@/components/fieldEditors/SelectFE";
import { directoryQueries } from "@/queries/directories/queries";
import { createStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { StorageMode } from "@/types/types";

import { StudyDestinationFE } from "../../StudyDestinationFE";
import type { DirectoryDestination } from "../../StudyDestinationFE/types";
import { useDefaultStudyDestination } from "../../StudyDestinationFE/useDefaultStudyDestination";
import { useRedirectToDestination } from "../../StudyDestinationFE/useRedirectToDestination";
import { refreshDirectoriesIfNeeded, toDirectoryPath } from "../../StudyDestinationFE/utils";
import StudyDestinationLayout from "../StudyDestinationLayout";
import { studyDestinationDialogPaperSx, studyDestinationRedirectSx } from "../styles";

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

const STORAGE_MODE_OPTIONS = [
  { value: StorageMode.FILESYSTEM, label: (t) => t("studies.storageMode.filesystem") },
  { value: StorageMode.DATABASE, label: (t) => t("studies.storageMode.database") },
] as const satisfies Options<StorageMode>;

function ImportStudyDialog({ open, onClose }: Props) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();
  const redirectToDestination = useRedirectToDestination();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());
  const defaultDestination = useDefaultStudyDestination(directories);

  const [destination, setDestination] = useState<DirectoryDestination>(defaultDestination);
  const [redirect, setRedirect] = useState(true);
  const [storageMode, setStorageMode] = useState(StorageMode.FILESYSTEM);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport: UploadDialogProps["onImport"] = async (file, onUploadProgress) => {
    const directoryPath = toDirectoryPath(destination, directories);

    await dispatch(
      createStudy({ file, onUploadProgress, directory: directoryPath, storageMode }),
    ).unwrap();
  };

  const handleImportComplete: UploadDialogProps["onImportComplete"] = async () => {
    const updatedDirectories = await refreshDirectoriesIfNeeded(
      queryClient,
      destination,
      directories,
    );

    if (redirect) {
      redirectToDestination(destination, updatedDirectories);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UploadDialog
      open={open}
      title={t("studies.importNewStudy")}
      dropzoneText={t("studies.importHint")}
      multiple
      onCancel={onClose}
      onImport={handleImport}
      onImportComplete={handleImportComplete}
      maxWidth="md"
      fullWidth
      slotProps={{ paper: { sx: studyDestinationDialogPaperSx } }}
      contentProps={{ sx: { px: 2, overflow: "hidden" } }}
    >
      {(uploadArea) => (
        <StudyDestinationLayout
          destination={
            <StudyDestinationFE
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              fillHeight
            />
          }
        >
          <Typography component="h3" variant="subtitle2">
            {t("global.general")}
          </Typography>
          <SelectFE
            label={t("studies.storageMode")}
            options={STORAGE_MODE_OPTIONS}
            value={storageMode}
            onChange={(event) => setStorageMode(event.target.value)}
            helperText={
              storageMode === StorageMode.DATABASE
                ? t("studies.storageMode.gemsCompatible")
                : undefined
            }
          />
          <CheckBoxFE
            value={redirect}
            onChange={(_event, checked) => setRedirect(checked)}
            label={t("studies.destination.redirectAfterImport")}
            size="small"
            sx={studyDestinationRedirectSx}
          />
          <Divider />
          {uploadArea}
        </StudyDestinationLayout>
      )}
    </UploadDialog>
  );
}

export default ImportStudyDialog;
