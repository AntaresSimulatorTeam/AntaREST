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

import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import DigestDialog from "@/components/dialogs/DigestDialog";
import LinearProgressWithLabel from "@/components/LinearProgressWithLabel";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import type { Job, JobStatus } from "@/services/api/launcher/jobs/types";
import { getStudyOutputs, killStudy } from "@/services/api/study";
import { convertUTCToLocalTime } from "@/services/utils";
import type { LaunchJobsProgress } from "@/types/types";
import type { EmptyObject } from "@/utils/tsUtils";
import BlockIcon from "@mui/icons-material/Block";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import { Step, StepLabel, Stepper, Tooltip, Typography } from "@mui/material";
import type { AxiosError } from "axios";
import moment from "moment";
import { useSnackbar } from "notistack";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import useStudy from "../../../-hooks/useStudy";
import LaunchJobLogView from "../../../../../tasks/-components/LaunchJobLogView";
import {
  CancelContainer,
  QontoConnector,
  QontoStepIconRoot,
  StepLabelRoot,
  StepLabelRow,
} from "./style";

export const ColorStatus = {
  running: "warning.main",
  pending: "grey.400",
  success: "success.main",
  failed: "error.main",
} as const;

const iconStyle = {
  m: 0.5,
  height: 22,
  cursor: "pointer",
};

function QontoStepIcon(props: { className: string | undefined; status: JobStatus }) {
  const { className, status } = props;
  return (
    <QontoStepIconRoot className={className}>
      <FiberManualRecordIcon
        sx={{
          width: 24,
          height: 24,
          color: ColorStatus[status],
        }}
      />
    </QontoStepIconRoot>
  );
}

type DialogState =
  | {
      type: "killJob" | "digest";
      job: Job;
    }
  | EmptyObject;

interface Props {
  jobs: Job[];
  jobsProgress: LaunchJobsProgress;
}

function JobStepper({ jobs, jobsProgress }: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [dialogState, setDialogState] = useState<DialogState>({});
  const study = useStudy();

  const { data: outputs, isLoading: outputsLoading } = usePromiseWithSnackbarError(
    () => getStudyOutputs(study.id),
    {
      disabled: study.archived,
      errorMessage: t("results.error.outputs"),
      deps: [study.id],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const canDisplayDigest = (job: Job) => {
    if (job.status !== "success") {
      return false;
    }

    const output = outputs?.find((output) => output.name === job.outputId);
    return !!output?.synthesis;
  };

  const closeDialog = () => setDialogState({});

  ////////////////////////////////////////////////////////////////
  // Actions
  ////////////////////////////////////////////////////////////////

  const killTask = async (jobId: Job["id"]) => {
    closeDialog();

    try {
      await killStudy(jobId);
    } catch (e) {
      enqueueErrorSnackbar(t("study.failtokilltask"), e as AxiosError);
    }
  };

  const copyId = (jobId: Job["id"]) => {
    try {
      navigator.clipboard.writeText(jobId);

      enqueueSnackbar(t("study.success.jobIdCopy"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(t("study.error.jobIdCopy"), e as AxiosError);
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Stepper
        activeStep={-1}
        orientation="vertical"
        connector={<QontoConnector />}
        sx={{ pr: 1, overflow: "auto" }}
      >
        {jobs.map((job) => (
          <Step key={job.id}>
            <StepLabel
              icon={<QontoStepIcon className={undefined} status={job.status} />}
              sx={{
                display: "flex",
                justifyContent: "flex-start",
                alignItems: "flex-start",
              }}
            >
              <StepLabelRoot>
                <StepLabelRow>
                  <Typography
                    variant="body2"
                    sx={{
                      height: "auto",
                      mx: 0,
                      boxSizing: "border-box",
                    }}
                  >
                    {moment(convertUTCToLocalTime(job.creationDate)).format(
                      "ddd, MMM D YYYY, HH:mm:ss",
                    )}
                    {job.completionDate &&
                      ` => ${moment(convertUTCToLocalTime(job.completionDate)).format(
                        "ddd, MMM D YYYY, HH:mm:ss",
                      )}`}
                  </Typography>
                </StepLabelRow>
                {job.outputId && <StepLabelRow mt={0.5}>{job.outputId}</StepLabelRow>}
                <StepLabelRow mt={1}>
                  <Tooltip title={t("study.copyJobId")}>
                    <ContentCopyIcon onClick={() => copyId(job.id)} sx={iconStyle} />
                  </Tooltip>
                  <LaunchJobLogView job={job} logButton logErrorButton />
                  {!outputsLoading && canDisplayDigest(job) && (
                    <Tooltip title="Digest">
                      <EqualizerIcon
                        onClick={() => setDialogState({ type: "digest", job })}
                        sx={iconStyle}
                      />
                    </Tooltip>
                  )}
                  {job.status === "running" && (
                    <CancelContainer>
                      <LinearProgressWithLabel
                        value={jobsProgress[job.id]}
                        tooltip="Progression"
                        sx={{ width: "30%" }}
                      />
                      <Tooltip title={t("study.killStudy")}>
                        <BlockIcon
                          onClick={() => setDialogState({ type: "killJob", job })}
                          sx={{
                            ...iconStyle,
                            color: "error.light",
                            "&:hover": { color: "error.dark" },
                          }}
                        />
                      </Tooltip>
                    </CancelContainer>
                  )}
                </StepLabelRow>
              </StepLabelRoot>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
      {dialogState.type === "killJob" && (
        <ConfirmationDialog
          open
          alert="warning"
          onConfirm={() => killTask(dialogState.job.id)}
          onCancel={closeDialog}
        >
          {t("study.question.killJob")}
        </ConfirmationDialog>
      )}
      {dialogState.type === "digest" && (
        <DigestDialog
          open
          studyId={dialogState.job.studyId}
          outputId={dialogState.job.outputId}
          onOk={closeDialog}
        />
      )}
    </>
  );
}

export default JobStepper;
