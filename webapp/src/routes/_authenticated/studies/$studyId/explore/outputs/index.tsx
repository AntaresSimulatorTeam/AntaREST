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

import DigestDialog from "@/components/dialogs/DigestDialog";
import ViewWrapper from "@/components/page/ViewWrapper";
import RouterLink from "@/components/router/RouterLink";
import useDialog from "@/hooks/useDialog";
import { jobQueries } from "@/queries/jobs/queries";
import { outputQueries } from "@/queries/outputs/queries";
import { isQueryListItemOptimistic } from "@/queries/utils";
import LaunchJobLogView from "@/routes/_authenticated/tasks/-components/LaunchJobLogView";
import type { Job } from "@/services/api/launcher/jobs/types";
import type { Output } from "@/services/api/studies/outputs/types";
import { downloadJobOutput } from "@/services/api/study";
import { convertUTCToLocalTime } from "@/services/utils";
import ArchiveIcon from "@mui/icons-material/Archive";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import DeleteIcon from "@mui/icons-material/Delete";
import DownloadIcon from "@mui/icons-material/Download";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import UnarchiveIcon from "@mui/icons-material/Unarchive";
import {
  Chip,
  CircularProgress,
  IconButton,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { useCallback } from "react";
import { useTranslation } from "react-i18next";
import useArchiveOutput from "./-hooks/useArchiveOutput";
import useDeleteOutput from "./-hooks/useDeleteOutput";
import useUnarchiveOutput from "./-hooks/useUnarchiveOutput";
import { selectJobsData, sortOutputsByCompletionDate, type OutputWithJob } from "./-utils";

export const Route = createFileRoute("/_authenticated/studies/$studyId/explore/outputs/")({
  loader: async ({ context, params: { studyId } }) => {
    await context.queryClient.ensureQueryData(jobQueries.list(studyId));
  },
  component: Outputs,
});

function Outputs() {
  const { studyId } = Route.useParams();
  const { t } = useTranslation();
  const { confirm, openDialog } = useDialog();
  const archiveOutput = useArchiveOutput();
  const unarchiveOutput = useUnarchiveOutput();
  const deleteOutput = useDeleteOutput();

  const {
    data: { jobsByOutputId, runningJobs },
  } = useSuspenseQuery({
    ...jobQueries.list(studyId),
    select: selectJobsData,
  });

  const selectOutputsWithJob = useCallback(
    (outputs: Output[]) => {
      return sortOutputsByCompletionDate(
        outputs.map((output) => ({
          ...output,
          job: jobsByOutputId[output.id] as Job | undefined,
        })),
      );
    },
    [jobsByOutputId],
  );

  const { data: outputsWithJob } = useSuspenseQuery({
    ...outputQueries.list(studyId),
    select: selectOutputsWithJob,
  });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleArchive = (output: Output) => {
    archiveOutput.mutate({ studyId, outputId: output.id });
  };

  const handleUnarchive = (output: Output) => {
    unarchiveOutput.mutate({ studyId, outputId: output.id });
  };

  const handleDelete = async (output: Output) => {
    const isConfirmed = await confirm({
      content: t("results.question.deleteOutput", { outputName: output.name }),
      alert: "error",
      titleIcon: DeleteIcon,
    });

    if (isConfirmed) {
      deleteOutput.mutate({ studyId, outputId: output.id });
    }
  };

  const handleDownload = (job: Job) => {
    // TODO: check if download work
    downloadJobOutput(job.id);
  };

  const handleOpenDigest = (job: Job) => {
    openDialog(({ onClose }) => (
      <DigestDialog open studyId={job.studyId} outputId={job.outputId} onOk={onClose} />
    ));
  };

  ////////////////////////////////////////////////////////////////
  // Render helpers
  ////////////////////////////////////////////////////////////////

  const renderCreationDate = (job: Job) => {
    return (
      <Stack gap={1}>
        <CalendarTodayIcon fontSize="extra-small" />
        {convertUTCToLocalTime(job.creationDate)}
      </Stack>
    );
  };

  const renderCompletionDate = (output: OutputWithJob) => {
    let completionDate: string | undefined;

    if (output.job?.completionDate) {
      completionDate = convertUTCToLocalTime(output.job.completionDate);
    }
    // If no related job or completion date is not available, try to parse date from output name
    else {
      const dateMatch = output.name.match(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})/);

      if (dateMatch) {
        const [, year, month, day, hour, minute] = dateMatch;
        completionDate = `${year}-${month}-${day} ${hour}:${minute}:00`;
      }
    }

    return (
      <Stack gap={1}>
        <EventAvailableIcon fontSize="extra-small" />
        {completionDate || t("global.unknown")}
      </Stack>
    );
  };

  const renderOutputNameColumn = (output: Output) => {
    const isOutputOptimistic = isQueryListItemOptimistic(output);
    const isDisabled = output.archived || isOutputOptimistic;

    return (
      <Stack gap={2}>
        {isOutputOptimistic && <CircularProgress size="1rem" color="inherit" />}
        <RouterLink
          color="inherit"
          underline={isDisabled ? "none" : "hover"}
          to="/studies/$studyId/explore/outputs/$outputId"
          params={{ studyId, outputId: output.id }}
          disabled={isDisabled}
        >
          {output.name}
        </RouterLink>
        {output.archived && <Chip label={t("study.archived")} size="small" color="warning" />}
      </Stack>
    );
  };

  const renderOutputActionButton = <T extends Output>(params: {
    output: T;
    tooltip: string;
    icon: React.ReactNode;
    onClick: (output: T) => void;
  }) => {
    return (
      <Tooltip title={params.tooltip}>
        <span>
          <IconButton
            onClick={() => params.onClick(params.output)}
            size="small"
            disabled={isQueryListItemOptimistic(params.output)}
          >
            {params.icon}
          </IconButton>
        </span>
      </Tooltip>
    );
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <ViewWrapper>
      <TableContainer component={Paper} elevation={2} sx={{ height: 1 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>{t("global.name")}</TableCell>
              <TableCell align="right">{t("global.user")}</TableCell>
              <TableCell align="right">{t("global.date")}</TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {/* Running jobs */}
            {runningJobs.length > 0 &&
              runningJobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell component="th" scope="row">
                    <Stack gap={2}>
                      <CircularProgress size="1rem" color="inherit" />
                      <Typography>{job.id}</Typography>
                    </Stack>
                  </TableCell>
                  <TableCell align="right">{job.owner?.name}</TableCell>
                  <TableCell align="right">
                    <Stack gap={2} justifyContent="flex-end">
                      {renderCreationDate(job)}
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <Stack justifyContent="flex-end">
                      <LaunchJobLogView job={job} logButton logErrorButton />
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}

            {/* Outputs  */}
            {outputsWithJob.length > 0 &&
              outputsWithJob.map((output) => (
                <TableRow key={output.id}>
                  <TableCell component="th" scope="row">
                    {renderOutputNameColumn(output)}
                  </TableCell>
                  <TableCell align="right">{output.job?.owner?.name}</TableCell>
                  <TableCell align="right">
                    <Stack gap={2} justifyContent="flex-end">
                      {output.job && renderCreationDate(output.job)}
                      {renderCompletionDate(output)}
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <Stack justifyContent="flex-end">
                      {/* Archive button */}
                      {output.archived === false &&
                        renderOutputActionButton({
                          output,
                          tooltip: t("global.archive"),
                          icon: <ArchiveIcon />,
                          onClick: handleArchive,
                        })}

                      {/* Unarchive button */}
                      {output.archived === true &&
                        renderOutputActionButton({
                          output,
                          tooltip: t("global.unarchive"),
                          icon: <UnarchiveIcon />,
                          onClick: handleUnarchive,
                        })}

                      {/* Download button (job) */}
                      {output.job && (
                        <Tooltip title={t("global.download")}>
                          <IconButton
                            onClick={() => output.job && handleDownload(output.job)}
                            size="small"
                          >
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                      )}

                      {/* Log viewer (job) */}
                      {output.job && <LaunchJobLogView job={output.job} logButton logErrorButton />}

                      {/* Digest button (job) */}
                      {output.synthesis && output.job && (
                        <Tooltip title="Digest">
                          <IconButton
                            onClick={() => output.job && handleOpenDigest(output.job)}
                            size="small"
                          >
                            <EqualizerIcon />
                          </IconButton>
                        </Tooltip>
                      )}

                      {/* Delete button */}
                      {renderOutputActionButton({
                        output,
                        tooltip: t("global.delete"),
                        icon: <DeleteIcon />,
                        onClick: handleDelete,
                      })}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}

            {/* No running jobs and no outputs */}
            {runningJobs.length === 0 && outputsWithJob.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>
                  <Typography sx={{ m: 2 }} align="center">
                    {t("results.noOutputs")}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </ViewWrapper>
  );
}
