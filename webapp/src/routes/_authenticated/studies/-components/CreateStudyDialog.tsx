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

import CustomScrollbar from "@/components/CustomScrollbar";
import FormDialog from "@/components/dialogs/FormDialog";
import CheckboxesTagsFE from "@/components/fieldEditors/CheckboxesTagsFE";
import SelectFE, { type Options } from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import { PUBLIC_MODE_LIST } from "@/components/utils/constants";
import { directoryQueries } from "@/queries/directories/queries";
import { createStudy } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import useAppSelector from "@/redux/hooks/useAppSelector";
import { getGroups, getLatestStudyVersion, getStudyVersions } from "@/redux/selectors";
import StudyDestinationFE from "@/routes/-shared/components/studies/StudyDestinationFE";
import { studyDestinationDialogContentSx } from "@/routes/-shared/components/studies/StudyDestinationFE/styles";
import type { DirectoryDestination } from "@/routes/-shared/components/studies/StudyDestinationFE/types";
import { useDefaultStudyDestination } from "@/routes/-shared/components/studies/StudyDestinationFE/useDefaultStudyDestination";
import { useRedirectToDestination } from "@/routes/-shared/components/studies/StudyDestinationFE/useRedirectToDestination";
import {
  refreshDirectoriesIfNeeded,
  toDirectoryPath,
} from "@/routes/-shared/components/studies/StudyDestinationFE/utils";
import { StorageMode, type StudyPublicMode } from "@/types/types";
import { validateStudyName } from "@/utils/studiesUtils";
import { getSemanticVersionOptions } from "@/utils/versionUtils";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import { Box, Button, IconButton } from "@mui/material";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useSnackbar } from "notistack";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";

interface FieldValues {
  name: string;
  version: string;
  publicMode: StudyPublicMode;
  groups: string[];
  tags: string[];
  storageMode: StorageMode;
  destination: DirectoryDestination;
}

interface Props {
  open: boolean;
  onClose: VoidFunction;
}

const STORAGE_MODE_OPTIONS = [
  { value: StorageMode.FILESYSTEM, label: (t) => t("studies.storageMode.filesystem") },
  { value: StorageMode.DATABASE, label: (t) => t("studies.storageMode.database") },
] as const satisfies Options<StorageMode>;

function CreateStudyDialog({ open, onClose }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { enqueueSnackbar, closeSnackbar } = useSnackbar();
  const versionList = useAppSelector(getStudyVersions);
  const latestVersion = useAppSelector(getLatestStudyVersion);
  const groupList = useAppSelector(getGroups);
  const dispatch = useAppDispatch();
  const queryClient = useQueryClient();
  const redirectToDestination = useRedirectToDestination();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());
  const defaultDestination = useDefaultStudyDestination(directories);

  const versionOptions = useMemo(() => getSemanticVersionOptions(versionList), [versionList]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    values: { name, destination, storageMode, ...rest },
  }: SubmitHandlerPlus<FieldValues>) => {
    const newStudy = await dispatch(
      createStudy({
        name: name.trim(),
        storageMode,
        directory:
          storageMode === StorageMode.FILESYSTEM
            ? toDirectoryPath(destination, directories)
            : undefined,
        ...rest,
      }),
    ).unwrap();

    const updatedDirectories =
      storageMode === StorageMode.FILESYSTEM
        ? await refreshDirectoriesIfNeeded(queryClient, destination, directories)
        : directories;

    return { newStudy, directories: updatedDirectories };
  };

  const handleSubmitSuccessful = (
    { values: { name, destination, storageMode } }: SubmitHandlerPlus<FieldValues>,
    { newStudy, directories: updatedDirectories }: Awaited<ReturnType<typeof handleSubmit>>,
  ) => {
    if (storageMode === StorageMode.FILESYSTEM) {
      redirectToDestination(destination, updatedDirectories);
    }

    const snackbarId = enqueueSnackbar(t("studies.success.createStudy", { name }), {
      variant: "success",
      preventDuplicate: false,
      action: (
        <>
          <Button
            onClick={() => {
              navigate({ to: "/studies/$studyId", params: { studyId: newStudy.id } });
              closeSnackbar(snackbarId);
            }}
          >
            {t("global.open")}
          </Button>
          <IconButton onClick={() => closeSnackbar(snackbarId)}>
            <CloseRoundedIcon />
          </IconButton>
        </>
      ),
    });

    onClose();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      title={t("studies.createNewStudy")}
      open={open}
      maxWidth="sm"
      contentProps={{ sx: studyDestinationDialogContentSx }}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      config={{
        defaultValues: {
          name: "",
          version: latestVersion || "",
          publicMode: "NONE",
          groups: [],
          tags: [],
          storageMode: StorageMode.FILESYSTEM,
          destination: defaultDestination,
        },
      }}
    >
      {({ control, watch }) => (
        <CustomScrollbar style={{ minHeight: 0 }}>
          <Box sx={{ p: 1 }}>
            <Fieldset fullFieldWidth>
              <StringFE
                label={t("studies.studyName")}
                name="name"
                control={control}
                rules={{ validate: validateStudyName }}
              />
              <SelectFE
                label={t("global.version")}
                options={versionOptions}
                name="version"
                control={control}
                rules={{ required: t("form.field.required") }}
              />
              <SelectFE
                label={t("studies.storageMode")}
                options={STORAGE_MODE_OPTIONS}
                name="storageMode"
                control={control}
                helperText={
                  watch("storageMode") === StorageMode.DATABASE
                    ? t("studies.storageMode.gemsCompatible")
                    : undefined
                }
              />
            </Fieldset>
            {watch("storageMode") === StorageMode.FILESYSTEM && (
              <Fieldset legend={t("studies.destination")} fullFieldWidth>
                <StudyDestinationFE name="destination" control={control} listHeight={200} />
              </Fieldset>
            )}
            <Fieldset legend={t("global.permission")} fullFieldWidth>
              <SelectFE
                label={t("study.publicMode")}
                options={PUBLIC_MODE_LIST.map((mode) => ({
                  label: t(mode.name),
                  value: mode.id,
                }))}
                name="publicMode"
                control={control}
              />
              <SelectFE
                label={t("global.group")}
                options={groupList.map((group) => group.name)}
                name="groups"
                control={control}
                multiple
              />
            </Fieldset>
            <Fieldset legend="Metadata" fullFieldWidth>
              <CheckboxesTagsFE
                options={[]}
                label={t("studies.enterTag")}
                freeSolo
                name="tags"
                control={control}
              />
            </Fieldset>
          </Box>
        </CustomScrollbar>
      )}
    </FormDialog>
  );
}

export default CreateStudyDialog;
