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

import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import type { DialogProps } from "@mui/material";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { useNavigate } from "@tanstack/react-router";
import FormDialog from "@/components/dialogs/FormDialog";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import CheckBoxFE from "@/components/fieldEditors/CheckBoxFE";
import { TREE_ROOT_NAME } from "@/components/utils/constants";
import { directoryQueries } from "@/queries/directories/queries";
import { updateStudyFilters } from "@/redux/ducks/studies";
import useAppDispatch from "@/redux/hooks/useAppDispatch";
import { getDescendantIds } from "@/routes/_authenticated/studies/-components/StudyTree/ManagedTree/utils";
import type { Directory } from "@/services/api/directories/types";
import { moveStudy } from "@/services/api/study";
import type { StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import StudyDestinationFE from "../../StudyDestinationFE";
import type { DirectoryValue } from "../../StudyDestinationFE/types";
import {
  computeAllowSubmitOnPristine,
  type FormValues,
  formSchema,
  getInitialDirectoryId,
  toDirectoryPath,
  resolveRedirectDirectoryId,
} from "./utils";

export interface MoveResult {
  directoryPath: string;
  directory: DirectoryValue;
  redirect: boolean;
  results: Array<PromiseSettledResult<unknown>>;
  directories: Directory[];
}

interface Props extends DialogProps {
  onClose: () => void;
  studies: StudyMetadata[];
}

function MoveStudyDialog({ open, onClose, studies }: Props) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const queryClient = useQueryClient();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const initialDirectoryId = getInitialDirectoryId(studies);
  const allowSubmitOnPristine = computeAllowSubmitOnPristine(initialDirectoryId, studies);

  const defaultValues = {
    directory: { id: initialDirectoryId, newDirectoryPath: "" },
    redirect: true,
  };

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async (data: SubmitHandlerPlus<FormValues>): Promise<MoveResult> => {
    const { directory, redirect } = formSchema.parse(data.values);

    // TODO: This adapter should be moved to the API layer when Tan stack migration is done.
    const directoryPath = toDirectoryPath(directory, directories);

    // Run moves sequentially so the first call creates any new directory
    // and subsequent calls reuse it (parallel calls would race and create duplicates).
    const results: Array<PromiseSettledResult<unknown>> = [];

    for (const study of studies) {
      try {
        const value = await moveStudy(study.id, directoryPath);
        results.push({ status: "fulfilled", value });
      } catch (reason) {
        results.push({ status: "rejected", reason });
      }
    }

    // When every single move failed, throw so FormDialog keeps the dialog open.
    if (results.every((result) => result.status === "rejected")) {
      throw toError((results[0] as PromiseRejectedResult).reason);
    }

    // Only invalidate when a new directory was created by the move
    // otherwise the existing cache is still valid.
    let updatedDirectories = directories;

    if (directory.newDirectoryPath) {
      await queryClient.invalidateQueries({
        queryKey: directoryQueries.list().queryKey,
      });

      updatedDirectories = queryClient.getQueryData(directoryQueries.list().queryKey) ?? [];
    }

    return { directoryPath, directory, redirect, results, directories: updatedDirectories };
  };

  const handleSubmitSuccessful = (
    _data: SubmitHandlerPlus<FormValues>,
    { directoryPath, directory, redirect, results, directories: updatedDirectories }: MoveResult,
  ) => {
    const failed = results.reduce<StudyMetadata[]>((acc, result, i) => {
      if (result.status === "rejected") {
        acc.push(studies[i]);
      }
      return acc;
    }, []);

    const succeededCount = studies.length - failed.length;

    onClose();

    if (failed.length > 0) {
      enqueueSnackbar(
        t("studies.warning.moveStudiesPartial", {
          count: failed.length,
          failed: failed.length,
          total: studies.length,
          details: failed.map((study) => `"${study.name}" (${study.id})`).join(", "),
        }),
        { variant: "warning" },
      );
    }

    if (succeededCount > 0) {
      enqueueSnackbar(
        t("studies.success.moveStudies", {
          count: succeededCount,
          path: directoryPath || TREE_ROOT_NAME,
          interpolation: { escapeValue: false },
        }),
        { variant: "success" },
      );
    }

    if (redirect) {
      const directoryId = resolveRedirectDirectoryId(directory, updatedDirectories);

      dispatch(
        updateStudyFilters({
          activeTree: "managed",
          managed: {
            directoryId,
            directoryIds: directoryId ? getDescendantIds(directoryId, updatedDirectories) : null,
          },
        }),
      );

      navigate({ to: "/studies" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={t("studies.moveStudies", { count: studies.length })}
      titleIcon={DriveFileMoveIcon}
      config={{ defaultValues }}
      maxWidth="sm"
      onSubmit={handleSubmit}
      onSubmitSuccessful={handleSubmitSuccessful}
      onCancel={onClose}
      allowSubmitOnPristine={allowSubmitOnPristine}
      submitButtonIcon={<DriveFileMoveIcon />}
      submitButtonText={t("global.move")}
    >
      {({ control }) => (
        <StudyDestinationFE name="directory" control={control}>
          <CheckBoxFE
            name="redirect"
            control={control}
            label={t("studies.destination.redirectAfterMove")}
            size="small"
            sx={{ color: "text.secondary" }}
          />
        </StudyDestinationFE>
      )}
    </FormDialog>
  );
}

export default MoveStudyDialog;
