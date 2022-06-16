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
} from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import CalendarTodayIcon from "@mui/icons-material/CalendarToday";
import EventAvailableIcon from "@mui/icons-material/EventAvailable";
import DownloadIcon from "@mui/icons-material/Download";
import * as R from "ramda";
import { useNavigate, useOutletContext } from "react-router-dom";
import { grey } from "@mui/material/colors";
import moment from "moment";
import usePromiseWithSnackbarError from "../../../../hooks/usePromiseWithSnackbarError";
import {
  downloadJobOutput,
  getStudyJobs,
  getStudyOutputs,
} from "../../../../services/api/study";
import {
  LaunchJob,
  StudyMetadata,
  StudyOutput,
} from "../../../../common/types";
import { convertUTCToLocalTime } from "../../../../services/utils";
import LaunchJobLogView from "../../../tasks/LaunchJobLogView";

interface OutputDetail {
  name: string;
  creationDate?: string;
  completionDate?: string;
  job?: LaunchJob;
}

const combineJobsAndOutputs = (
  jobs: LaunchJob[],
  outputs: StudyOutput[]
): OutputDetail[] => {
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
    };
    if (relatedJob) {
      outputDetail.completionDate = relatedJob.completionDate;
      outputDetail.creationDate = relatedJob.creationDate;
      outputDetail.job = relatedJob;
    } else {
      const dateComponents = output.name.match(
        "(\\d{4})(\\d{2})(\\d{2})-(\\d{2})(\\d{2}).*"
      );
      if (dateComponents) {
        outputDetail.completionDate = `${dateComponents[1]}-${dateComponents[2]}-${dateComponents[3]} ${dateComponents[4]}:${dateComponents[5]}`;
      }
    }
    return outputDetail;
  });
  return runningJobs.concat(outputDetails);
};

function Results() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const { t } = useTranslation();
  const navigate = useNavigate();

  const { data: studyJobs, isLoading: studyJobsLoading } =
    usePromiseWithSnackbarError(() => getStudyJobs(study.id), {
      errorMessage: t("results.error.jobs"),
      deps: [study.id],
    });

  const { data: studyOutputs, isLoading: studyOutputsLoading } =
    usePromiseWithSnackbarError(() => getStudyOutputs(study.id), {
      errorMessage: t("results.error.outputs"),
      deps: [study.id],
    });

  const outputs = useMemo(() => {
    if (studyJobs && studyOutputs) {
      return combineJobsAndOutputs(studyJobs, studyOutputs).sort((a, b) => {
        if (!a.completionDate || !b.completionDate) {
          if (!a.completionDate && !b.completionDate) {
            return moment(a.creationDate).isAfter(moment(b.creationDate))
              ? -1
              : 1;
          }
          if (!a.completionDate) {
            return -1;
          }
          return 1;
        }
        return moment(a.completionDate).isAfter(moment(b.completionDate))
          ? -1
          : 1;
      });
    }
    return [];
  }, [studyJobs, studyOutputs]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleOutputNameClick = (outputName: string) => () => {
    navigate(`/studies/${study.id}/explore/results/${outputName}`);
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
                  color: grey[500],
                },
              }}
            >
              <TableCell>{t("global.name")}</TableCell>
              <TableCell align="right">
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="flex-end"
                >
                  {t("global.date")}
                </Box>
              </TableCell>
              <TableCell align="right">{t("tasks.action")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {R.cond([
              [
                () => studyJobsLoading && studyOutputsLoading,
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
                              onClick={handleOutputNameClick(row.name)}
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
                              color: grey[500],
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
                          <Box
                            display="flex"
                            alignItems="center"
                            justifyContent="flex-end"
                          >
                            <Box>
                              {row.completionDate && row.job ? (
                                <Tooltip title={t("global.download") as string}>
                                  <DownloadIcon
                                    sx={{
                                      fontSize: 22,
                                      color: "action.active",
                                      cursor: "pointer",
                                      "&:hover": { color: "action.hover" },
                                    }}
                                    onClick={() => {
                                      if (row.job) {
                                        downloadJobOutput(row.job.id);
                                      }
                                    }}
                                  />
                                </Tooltip>
                              ) : (
                                <Box />
                              )}
                            </Box>
                            {row.job && (
                              <LaunchJobLogView
                                job={row.job}
                                logButton
                                logErrorButton
                              />
                            )}
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
    </Box>
  );
}

export default Results;
