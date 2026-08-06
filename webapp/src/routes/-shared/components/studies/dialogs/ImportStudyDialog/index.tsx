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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";

import UploadDialog, { type UploadDialogProps } from "@/components/dialogs/UploadDialog";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";
import SelectFE from "@/components/fieldEditors/SelectFE";
import { directoryQueries } from "@/queries/directories/queries";
import { createStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { StorageMode } from "@/types/types";

import { StudyDestinationFE } from "../../StudyDestinationFE";
import type { DirectoryDestination } from "../../StudyDestinationFE/types";
import { refreshDirectoriesIfNeeded, toDirectoryPath } from "../../StudyDestinationFE/utils";
import { useRedirectToDestination } from "../../StudyDestinationFE/useRedirectToDestination";

const ROOT_DESTINATION: DirectoryDestination = { directoryId: null, newSubdirectoriesPath: "" };

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

function ImportStudyDialog({ open, onClose }: Props) {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();
  const redirectToDestination = useRedirectToDestination();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const [destination, setDestination] = useState<DirectoryDestination>(ROOT_DESTINATION);
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
      PaperProps={{ sx: { height: "100%" } }}
      extraContent={
        <>
          <StudyDestinationFE
            value={destination}
            onChange={(event) => setDestination(event.target.value)}
            fillHeight
          />
          <SelectFE
            label={t("studies.storageMode")}
            options={[
              { value: StorageMode.FILESYSTEM, label: t("studies.storageMode.filesystem") },
              { value: StorageMode.DATABASE, label: t("studies.storageMode.database") },
            ]}
            value={storageMode}
            onChange={(event) => setStorageMode(event.target.value as StorageMode)}
            helperText={
              storageMode === StorageMode.DATABASE
                ? t("studies.storageMode.gemsCompatible")
                : undefined
            }
            size="small"
          />
          <CheckBoxFE
            value={redirect}
            onChange={(_event, checked) => setRedirect(checked)}
            label={t("studies.destination.redirectAfterImport")}
            size="small"
            sx={{ color: "text.secondary" }}
          />
        </>
      }
    />
  );
}

export default ImportStudyDialog;
