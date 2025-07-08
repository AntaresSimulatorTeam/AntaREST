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

import ArchiveIcon from "@mui/icons-material/Archive";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import DownloadIcon from "@mui/icons-material/Download";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import UnarchiveIcon from "@mui/icons-material/Unarchive";
import {
  Box,
  CircularProgress,
  Link as MuiLink,
  Paper,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useOutletContext } from "react-router-dom";
import DigestDialog from "@/components/common/dialogs/DigestDialog";
import ViewWrapper from "@/components/common/page/ViewWrapper";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import {
  archiveOutput,
  deleteOutput,
  downloadJobOutput,
  getStudyJobs,
  getStudyOutputs,
  unarchiveOutput,
} from "../../../../../services/api/study";
import { convertUTCToLocalTime } from "../../../../../services/utils";
import type { LaunchJob, StudyMetadata, StudyOutput } from "../../../../../types/types";
import type { EmptyObject } from "../../../../../utils/tsUtils";
import ConfirmationDialog from "../../../../common/dialogs/ConfirmationDialog";
import LaunchJobLogView from "../../../Tasks/LaunchJobLogView";
import { compareDesc, parseISO } from "date-fns";
import { toError } from "@/utils/fnUtils";

interface OutputDetail {
  name: string;
  creationDate?: string;
  completionDate?: string;
  job?: LaunchJob;
  output?: StudyOutput;
  archived?: boolean;
  isRunning: boolean;
}

interface ConfirmDeleteDialog {
  type: "confirmDelete";
  data: string;
}

interface DigestDialog {
  type: "digest";
  data: LaunchJob;
}

type DialogState = ConfirmDeleteDialog | DigestDialog | EmptyObject;

const iconStyle = {
  fontSize: 22,
  color: "action.active",
  cursor: "pointer",
};

function Results() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [dialogState, setDialogState] = useState<DialogState>({});

  const { data: studyJobs, isLoading: studyJobsLoading } = usePromiseWithSnackbarError(
    () => getStudyJobs(study.id),
    {
      errorMessage: t("results.error.jobs"),
      deps: [study.id],
    },
  );

  const {
    data: studyOutputs,
    isLoading: studyOutputsLoading,
    reload: reloadOutputs,
  } = usePromiseWithSnackbarError(() => getStudyOutputs(study.id), {
    errorMessage: t("results.error.outputs"),
    deps: [study.id],
  });

  const isLoading = studyJobsLoading || studyOutputsLoading;

  const outputs = useMemo(() => {
    if (!studyJobs || !studyOutputs) {
      return [];
    }

    const outputMap = new Map<string, OutputDetail>();
    const jobsByOutputId = new Map<string, LaunchJob>();

    studyJobs.forEach((job) => {
      if (job.outputId) {
        jobsByOutputId.set(job.outputId, job);
      }
    });

    // Process completed outputs
    studyOutputs.forEach((output) => {
      const relatedJob = jobsByOutputId.get(output.name);

      const outputDetail: OutputDetail = {
        name: output.name,
        archived: output.archived,
        output,
        isRunning: false,
        completionDate: relatedJob?.completionDate,
        creationDate: relatedJob?.creationDate,
        job: relatedJob,
      };

      // If no related job, try to parse date from output name
      if (!relatedJob && !outputDetail.completionDate) {
        const dateMatch = output.name.match(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})/);

        if (dateMatch) {
          const [, year, month, day, hour, minute] = dateMatch;
          outputDetail.completionDate = `${year}-${month}-${day} ${hour}:${minute}`;
        }
      }

      outputMap.set(output.name, outputDetail);
    });

    // Process running jobs
    studyJobs.forEach((job) => {
      if (!job.completionDate) {
        outputMap.set(job.id, {
          name: job.id,
          creationDate: job.creationDate,
          job,
          isRunning: true,
        });
      }
    });

    // Sort by date (most recent first)
    return Array.from(outputMap.values()).sort((a, b) => {
      const dateA = a.completionDate || a.creationDate;
      const dateB = b.completionDate || b.creationDate;

      if (!dateA || !dateB) {
        return a.isRunning ? -1 : b.isRunning ? 1 : 0;
      }

      return compareDesc(parseISO(dateA), parseISO(dateB));
    });
  }, [studyJobs, studyOutputs]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleArchiveToggle = async (output: OutputDetail) => {
    if (output.archived === undefined) {
      return;
    }

    const handler = output.archived
      ? () => unarchiveOutput(study.id, output.name)
      : () => archiveOutput(study.id, output.name);

    const errorMessage = output.archived
      ? "studies.error.unarchiveOutput"
      : "studies.error.archiveOutput";

    try {
      await handler();
      reloadOutputs();
    } catch (error) {
      enqueueErrorSnackbar(t(errorMessage, { outputname: output.name }), toError(error));
    }
  };

  const handleDeleteOutput = async (outputName: string) => {
    setDialogState({});
    await deleteOutput(study.id, outputName);
    reloadOutputs();
  };

  const handleDownload = (job?: LaunchJob) => {
    if (job) {
      downloadJobOutput(job.id);
    }
  };

  const openDigestDialog = (job: LaunchJob) => {
    setDialogState({ type: "digest", data: job });
  };

  const openDeleteDialog = (outputName: string) => {
    setDialogState({ type: "confirmDelete", data: outputName });
  };

  const closeDialog = () => setDialogState({});

  ////////////////////////////////////////////////////////////////
  // Render helpers
  ////////////////////////////////////////////////////////////////

  const renderDateCell = (output: OutputDetail) => (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        flexDirection: "column",
        fontSize: "0.85rem",
      }}
    >
      {output.creationDate && (
        <Box width="168px" display="flex" justifyContent="space-between" alignItems="center">
          <CalendarTodayIcon sx={{ fontSize: 16, mr: 0.5 }} />
          {convertUTCToLocalTime(output.creationDate)}
        </Box>
      )}
      {output.completionDate && (
        <Box width="168px" display="flex" justifyContent="space-between" alignItems="center">
          <EventAvailableIcon sx={{ fontSize: 16, mr: 0.5 }} />
          {convertUTCToLocalTime(output.completionDate)}
        </Box>
      )}
    </Box>
  );

  const renderActions = (output: OutputDetail) => (
    <Box display="flex" alignItems="center" justifyContent="flex-end">
      {/* Archive/Unarchive button */}
      {output.archived !== undefined && (
        <Box sx={{ height: "24px", margin: 0.5 }}>
          <Tooltip title={t(output.archived ? "global.unarchive" : "global.archive") as string}>
            {output.archived ? (
              <UnarchiveIcon sx={iconStyle} onClick={() => handleArchiveToggle(output)} />
            ) : (
              <ArchiveIcon sx={iconStyle} onClick={() => handleArchiveToggle(output)} />
            )}
          </Tooltip>
        </Box>
      )}

      {/* Download button */}
      {output.completionDate && output.job && (
        <Box sx={{ height: "24px", margin: 0.5 }}>
          <Tooltip title={t("global.download") as string}>
            <DownloadIcon sx={iconStyle} onClick={() => handleDownload(output.job)} />
          </Tooltip>
        </Box>
      )}

      {/* Log viewer */}
      {output.job && <LaunchJobLogView job={output.job} logButton logErrorButton />}

      {/* Digest button */}
      {output.job?.status === "success" && output.output?.settings?.output?.synthesis && (
        <Box sx={{ height: "24px", margin: 0.5 }}>
          <Tooltip title="Digest">
            <EqualizerIcon
              sx={iconStyle}
              onClick={() => output.job && openDigestDialog(output.job)}
            />
          </Tooltip>
        </Box>
      )}

      {/* Delete button */}
      <Box sx={{ height: "24px", margin: 0.5 }}>
        <Tooltip title={t("global.delete") as string}>
          <DeleteForeverIcon
            sx={{
              ...iconStyle,
              "&:hover": { color: "error.light" },
            }}
            onClick={() => openDeleteDialog(output.name)}
          />
        </Tooltip>
      </Box>
    </Box>
  );

  const renderNameCell = (output: OutputDetail) => {
    if (output.isRunning) {
      return (
        <Box sx={{ display: "flex", alignItems: "center" }}>
          <CircularProgress size="1rem" color="inherit" sx={{ mr: 1 }} />
          <Typography>{output.name}</Typography>
        </Box>
      );
    }

    return (
      <MuiLink
        color="inherit"
        underline="hover"
        component={Link}
        to={`/studies/${study.id}/explore/results/${encodeURIComponent(output.name)}`}
      >
        {output.name}
      </MuiLink>
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
              <TableCell align="right">{t("global.date")}</TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 3 }).map((_, index) => (
                <TableRow key={`loading-row-${Date.now()}-${index}`}>
                  <TableCell colSpan={3}>
                    <Skeleton sx={{ width: 1, height: 50 }} />
                  </TableCell>
                </TableRow>
              ))
            ) : outputs.length > 0 ? (
              outputs.map((output) => (
                <TableRow key={output.name}>
                  <TableCell component="th" scope="row">
                    {renderNameCell(output)}
                  </TableCell>
                  <TableCell align="right">{renderDateCell(output)}</TableCell>
                  <TableCell align="right">{renderActions(output)}</TableCell>
                </TableRow>
              ))
            ) : (
              // Empty state
              <TableRow>
                <TableCell colSpan={3}>
                  <Typography sx={{ m: 2 }} align="center">
                    {t("results.noOutputs")}
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialogs */}
      {dialogState.type === "confirmDelete" && (
        <ConfirmationDialog
          open
          onConfirm={() => handleDeleteOutput(dialogState.data)}
          onCancel={closeDialog}
        >
          {t("results.question.deleteOutput", { outputname: dialogState.data })}
        </ConfirmationDialog>
      )}

      {dialogState.type === "digest" && (
        <DigestDialog
          open
          studyId={dialogState.data.studyId}
          outputId={dialogState.data.outputId}
          onOk={closeDialog}
        />
      )}
    </ViewWrapper>
  );
}

export default Results;
