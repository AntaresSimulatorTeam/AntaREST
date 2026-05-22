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

import FormDialog from "@/components/dialogs/FormDialog";
import FieldSkeleton from "@/components/fieldEditors/FieldSkeleton";
import SelectFE from "@/components/fieldEditors/SelectFE";
import StringFE from "@/components/fieldEditors/StringFE";
import Fieldset from "@/components/Fieldset";
import type { SubmitHandlerPlus } from "@/components/Form/types";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import { directoryQueries } from "@/queries/directories/queries";
import { outputQueries } from "@/queries/outputs/queries";
import { copyStudy } from "@/services/api/studies";
import type { Output } from "@/services/api/studies/outputs/types";
import { getTask } from "@/services/api/tasks";
import type { OutputDetails, StudyMetadata } from "@/types/types";
import { toError } from "@/utils/fnUtils";
import { validateStudyName } from "@/utils/studiesUtils";
import FileCopyOutlinedIcon from "@mui/icons-material/FileCopyOutlined";
import SaveAsIcon from "@mui/icons-material/SaveAs";
import { useQuery, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import StudyDestinationFE from "../StudyDestinationFE";
import type { DirectoryDestination } from "../StudyDestinationFE/types";
import { toDirectoryPath } from "../StudyDestinationFE/utils";

interface Props {
  study: StudyMetadata;
  open: boolean;
  onClose: VoidFunction;
}

interface DefaultValues {
  studyName: string;
  destination: DirectoryDestination;
  outputIds?: Array<OutputDetails["name"]>;
}

function selectOutputsData(outputs: Output[]) {
  const outputOptions = outputs.map((output) => ({
    value: output.id,
    label: output.name,
  }));

  const defaultOutputIds = outputs.map((output) => output.id);

  return { outputOptions, defaultOutputIds };
}

function CopyStudyDialog({ study, open, onClose }: Props) {
  const { t } = useTranslation();
  const isVariant = study.type === "variantstudy";
  const Icon = isVariant ? SaveAsIcon : FileCopyOutlinedIcon;
  const queryClient = useQueryClient();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { data: directories } = useSuspenseQuery(directoryQueries.list());

  const {
    data: { outputOptions, defaultOutputIds } = { outputOptions: [], defaultOutputIds: [] },
    isPending: isOutputsPending,
    isError: isOutputsError,
    isSuccess: isOutputsSuccess,
  } = useQuery({
    ...outputQueries.list(study.id),
    select: selectOutputsData,
  });

  const defaultValues: DefaultValues = {
    studyName: `${study.name} (${t("studies.copySuffix")})`,
    destination: { directoryId: study.directoryId ?? null, newSubdirectoriesPath: "" },
  };

  ////////////////////////////////////////////////////////////////
  // Event handlers
  ////////////////////////////////////////////////////////////////

  const handleSubmit = async ({
    values: { studyName, destination, outputIds = [] },
  }: SubmitHandlerPlus<DefaultValues>) => {
    // TODO: This should be moved to the API layer when Tan stack migration is done.
    const directoryPath = toDirectoryPath(destination, directories);

    const taskId = await copyStudy({
      studyId: study.id,
      studyName: studyName.trim(),
      destinationFolder: directoryPath,
      outputIds,
    });

    // Poll task completion in the background, then refresh
    // the directory list so the dialog is not blocked while the task runs.
    getTask({ id: taskId, waitForCompletion: true })
      .then(() => {
        if (destination.newSubdirectoriesPath) {
          queryClient.invalidateQueries({ queryKey: directoryQueries.list().queryKey });
        }
      })
      .catch((err) => {
        enqueueErrorSnackbar(t("studies.error.copyStudy"), toError(err));
      });

    return taskId;
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <FormDialog
      open={open}
      title={isVariant ? t("study.copyVariant") : t("global.copy")}
      titleIcon={Icon}
      maxWidth="sm"
      submitButtonIcon={<Icon />}
      submitButtonText={isVariant ? t("global.record") : t("global.copy")}
      onCancel={onClose}
      onSubmit={handleSubmit}
      onSubmitSuccessful={onClose}
      config={{ defaultValues }}
      allowSubmitOnPristine
    >
      {({ control, setValue }) => (
        <Fieldset fullFieldWidth>
          <StringFE
            name="studyName"
            label={t("global.name")}
            control={control}
            rules={{ validate: validateStudyName }}
            autoFocus
          />
          <StudyDestinationFE name="destination" control={control} />
          {/* Outputs field */}
          {isOutputsPending && (
            <FieldSkeleton>
              <SelectFE value="" />
            </FieldSkeleton>
          )}
          {isOutputsError && (
            <SelectFE
              label={t("global.outputs")}
              helperText={t("study.error.listOutputs")}
              error
              disabled
            />
          )}
          {isOutputsSuccess && (
            <SelectFE
              name="outputIds"
              control={control}
              label={t("global.outputs")}
              defaultValue={defaultOutputIds}
              options={outputOptions}
              startCaseLabel={false}
              multiple
              onSelectAllOptions={(values) => setValue("outputIds", values)}
              onDeselectAllOptions={() => setValue("outputIds", [])}
            />
          )}
        </Fieldset>
      )}
    </FormDialog>
  );
}

export default CopyStudyDialog;
