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

import {
  Box,
  CircularProgress,
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
  colors,
} from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import ArchiveIcon from "@mui/icons-material/Archive";
import UnarchiveIcon from "@mui/icons-material/Unarchive";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteForeverIcon from "@mui/icons-material/DeleteForever";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import * as R from "ramda";
import { useNavigate, useOutletContext } from "react-router-dom";
import moment from "moment";
import type { AxiosError } from "axios";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import {
  archiveOutput,
  deleteOutput,
  downloadJobOutput,
  getStudyJobs,
  getStudyOutputs,
  unarchiveOutput,
} from "../../../../../services/api/study";
import type { LaunchJob, StudyMetadata, StudyOutput } from "../../../../../types/types";
import { convertUTCToLocalTime } from "../../../../../services/utils";
import LaunchJobLogView from "../../../Tasks/LaunchJobLogView";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "../../../../common/dialogs/ConfirmationDialog";
import type { EmptyObject } from "../../../../../utils/tsUtils";
import DigestDialog from "@/components/common/dialogs/DigestDialog";

interface OutputDetail {
  name: string;
  creationDate?: string;
  completionDate?: string;
  job?: LaunchJob;
  output?: StudyOutput;
  archived?: boolean;
}

type DialogState =
  | {
      type: "confirmDelete";
      data: string;
    }
  | {
      type: "digest";
      data: LaunchJob;
    }
  | EmptyObject;

const combineJobsAndOutputs = (jobs: LaunchJob[], outputs: StudyOutput[]): OutputDetail[] => {
  const runningJobs: OutputDetail[] = jobs
    .filter((job) => !job.completionDate)
    .map((job) => {
      return {
        name: job.id,
        creationDate: job.creationDate,
        job,
      };
    });
  const outputDetails = outputs.map((output) => {
    const relatedJob = jobs.find((job) => job.outputId === output.name);
    const outputDetail: OutputDetail = {
      name: output.name,
      archived: output.archived,
      output,
    };
    if (relatedJob) {
      outputDetail.completionDate = relatedJob.completionDate;
      outputDetail.creationDate = relatedJob.creationDate;
      outputDetail.job = relatedJob;
    } else {
      const dateComponents = output.name.match("(\\d{4})(\\d{2})(\\d{2})-(\\d{2})(\\d{2}).*");
      if (dateComponents) {
        outputDetail.completionDate = `${dateComponents[1]}-${dateComponents[2]}-${dateComponents[3]} ${dateComponents[4]}:${dateComponents[5]}`;
      }
    }
    return outputDetail;
  });
  return runningJobs.concat(outputDetails);
};

const iconStyle = {
  fontSize: 22,
  color: "action.active",
  cursor: "pointer",
  "&:hover": { color: "action.hover" },
};

function Results() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
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

  const outputs = useMemo(() => {
    if (studyJobs && studyOutputs) {
      return combineJobsAndOutputs(studyJobs, studyOutputs).sort((a, b) => {
        if (!a.completionDate || !b.completionDate) {
          if (!a.completionDate && !b.completionDate) {
            return moment(a.creationDate).isAfter(moment(b.creationDate)) ? -1 : 1;
          }
          if (!a.completionDate) {
            return -1;
          }
          return 1;
        }
        return moment(a.completionDate).isAfter(moment(b.completionDate)) ? -1 : 1;
      });
    }
    return [];
  }, [studyJobs, studyOutputs]);

  const renderArchiveTool = (output: OutputDetail) => {
    if (output.archived === undefined) {
      return <div />;
    }
    const title = output.archived ? "global.unarchive" : "global.archive";
    const errorMessage = output.archived
      ? "studies.error.unarchiveOutput"
      : "studies.error.archiveOutput";
    const Component = output.archived ? UnarchiveIcon : ArchiveIcon;
    const handler = output.archived
      ? () => unarchiveOutput(study.id, output.name)
      : () => archiveOutput(study.id, output.name);
    return (
      <Box sx={{ height: "24px", margin: 0.5 }}>
        <Tooltip title={t(title) as string}>
          <Component
            sx={iconStyle}
            onClick={async () => {
              handler().catch((e) => {
                enqueueErrorSnackbar(t(errorMessage, { outputname: output.name }), e as AxiosError);
              });
            }}
          />
        </Tooltip>
      </Box>
    );
  };

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const closeDialog = () => setDialogState({});

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOutputNameClick = (output: OutputDetail) => () => {
    navigate(`/studies/${study.id}/explore/results/${output.name}`, {
      state: output.output,
    });
  };

  const handleDeleteOutput = async (outputName: string) => {
    closeDialog();
    await deleteOutput(study.id, outputName);
    reloadOutputs();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        width: 1,
        height: 1,
        overflow: "auto",
        p: 2,
      }}
    >
      <TableContainer component={Paper}>
        <Table sx={{ width: 1, height: "90%" }} aria-label="simple table">
          <TableHead>
            <TableRow
              sx={{
                "& td, & th": {
                  borderBottom: "1px solid",
                  borderColor: "divider",
                  color: colors.grey[500],
                },
              }}
            >
              <TableCell>{t("global.name")}</TableCell>
              <TableCell align="right">
                <Box display="flex" alignItems="center" justifyContent="flex-end">
                  {t("global.date")}
                </Box>
              </TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {R.cond([
              [
                () => studyJobsLoading || studyOutputsLoading,
                () => (
                  <>
                    {Array.from({ length: 3 }, (v, k) => k).map((v) => (
                      <TableRow
                        key={`sk-${v}`}
                        sx={{
                          "& td, & th": {
                            borderColor: "divider",
                          },
                          "&:last-child > td, &:last-child > th": {
                            border: 0,
                          },
                        }}
                      >
                        <TableCell colSpan={3} scope="row">
                          <Skeleton sx={{ width: 1, height: 50 }} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </>
                ),
              ],
              [
                () => outputs.length > 0,
                () => (
                  <>
                    {outputs.map((row) => (
                      <TableRow
                        key={`job-${row.name}`}
                        sx={{
                          "& td, & th": {
                            borderColor: "divider",
                          },
                          "&:last-child > td, &:last-child > th": {
                            border: 0,
                          },
                        }}
                      >
                        <TableCell component="th" scope="row">
                          {row.completionDate ? (
                            <Typography
                              sx={{
                                "&:hover": { textDecoration: "underline" },
                                cursor: "pointer",
                              }}
                              onClick={handleOutputNameClick(row)}
                            >
                              {row.name}
                            </Typography>
                          ) : (
                            <Box sx={{ display: "flex", alignItems: "center" }}>
                              <CircularProgress
                                size="1rem"
                                color="inherit"
                                sx={{
                                  mr: 1,
                                }}
                              />
                              <Typography>{row.name}</Typography>
                            </Box>
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "flex-end",
                              justifyContent: "center",
                              flexDirection: "column",
                              color: colors.grey[500],
                              fontSize: "0.85rem",
                            }}
                          >
                            {row.creationDate && (
                              <Box
                                width="168px"
                                display="flex"
                                justifyContent="space-between"
                                alignItems="center"
                              >
                                <CalendarTodayIcon
                                  sx={{
                                    fontSize: 16,
                                    marginRight: "0.5em",
                                  }}
                                />
                                {convertUTCToLocalTime(row.creationDate)}
                              </Box>
                            )}
                            <Box
                              width="168px"
                              display="flex"
                              justifyContent="space-between"
                              alignItems="center"
                            >
                              {row.completionDate && (
                                <>
                                  <EventAvailableIcon
                                    sx={{
                                      fontSize: 16,
                                      marginRight: "0.5em",
                                    }}
                                  />
                                  {convertUTCToLocalTime(row.completionDate)}
                                </>
                              )}
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Box display="flex" alignItems="center" justifyContent="flex-end">
                            {renderArchiveTool(row)}
                            {row.completionDate && row.job && (
                              <Box sx={{ height: "24px", margin: 0.5 }}>
                                <Tooltip title={t("global.download") as string}>
                                  <DownloadIcon
                                    sx={iconStyle}
                                    onClick={() => {
                                      if (row.job) {
                                        downloadJobOutput(row.job.id);
                                      }
                                    }}
                                  />
                                </Tooltip>
                              </Box>
                            )}

                            {row.job && <LaunchJobLogView job={row.job} logButton logErrorButton />}
                            {row.job?.status === "success" && (
                              <Tooltip title="Digest">
                                <EqualizerIcon
                                  onClick={() => {
                                    setDialogState({
                                      type: "digest",
                                      data: row.job as LaunchJob,
                                    });
                                  }}
                                  sx={iconStyle}
                                />
                              </Tooltip>
                            )}
                            <Box sx={{ height: "24px", margin: 0.5 }}>
                              <Tooltip title={t("global.delete") as string}>
                                <DeleteForeverIcon
                                  sx={{
                                    ...iconStyle,
                                    "&:hover": { color: "error.light" },
                                  }}
                                  onClick={() => {
                                    setDialogState({
                                      type: "confirmDelete",
                                      data: row.name,
                                    });
                                  }}
                                />
                              </Tooltip>
                            </Box>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                  </>
                ),
              ],
              [
                R.T,
                () => (
                  <TableRow
                    key="job-none"
                    sx={{
                      "& td, & th": {
                        borderColor: "divider",
                      },
                      "&:last-child > td, &:last-child > th": {
                        border: 0,
                      },
                    }}
                  >
                    <TableCell colSpan={3} scope="row">
                      <Typography sx={{ m: 2 }} align="center">
                        {t("results.noOutputs")}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ),
              ],
            ])()}
          </TableBody>
        </Table>
      </TableContainer>
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
    </Box>
  );
}

export default Results;
