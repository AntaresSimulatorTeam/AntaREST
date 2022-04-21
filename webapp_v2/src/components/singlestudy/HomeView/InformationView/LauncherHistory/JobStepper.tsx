import Box from "@mui/material/Box";
import Stepper from "@mui/material/Stepper";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import InfoIcon from "@mui/icons-material/Info";
import DescriptionIcon from "@mui/icons-material/Description";
import CancelIcon from "@mui/icons-material/Cancel";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import {
  StepConnector,
  stepConnectorClasses,
  StepIconProps,
  styled,
  Tooltip,
} from "@mui/material";
import moment from "moment";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { AxiosError } from "axios";
import { JobStatus, LaunchJob } from "../../../../../common/types";
import { convertUTCToLocalTime } from "../../../../../services/utils";
import { scrollbarStyle } from "../../../../../theme";
import ConfirmationModal from "../../../../common/ConfirmationModal";
import { killStudy } from "../../../../../services/api/study";
import enqueueErrorSnackbar from "../../../../common/ErrorSnackBar";

const QontoConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.disabled}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      height: "20px",
    },
  },
}));

const QontoStepIconRoot = styled("div")(({ theme }) => ({
  color: theme.palette.mode === "dark" ? theme.palette.grey[700] : "#eaeaf0",
  display: "flex",
  width: "24px",
  justifyContent: "center",
  alignItems: "center",
  "& .QontoStepIcon-inprogress": {
    width: 16,
    height: 16,
    color: theme.palette.primary.main,
  },
}));

const ColorStatus = {
  running: "primary.main",
  pending: "primary.main",
  success: "success.main",
  failed: "error.main",
};

function QontoStepIcon(props: {
  className: string | undefined;
  status: JobStatus;
}) {
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

interface Props {
  jobs: Array<LaunchJob>;
}

export default function VerticalLinearStepper(props: Props) {
  const { jobs } = props;
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const [jobIdKill, setJobIdKill] = useState<string>();

  const openConfirmModal = (jobId: string) => {
    setOpenConfirmationModal(true);
    setJobIdKill(jobId);
  };

  const killTask = (jobId: string) => {
    (async () => {
      try {
        await killStudy(jobId);
      } catch (e) {
        enqueueErrorSnackbar(
          enqueueSnackbar,
          t("singlestudy:failtokilltask"),
          e as AxiosError
        );
      }
      setOpenConfirmationModal(false);
    })();
  };

  const copyId = (jobId: string): void => {
    try {
      navigator.clipboard.writeText(jobId);
      enqueueSnackbar(t("singlestudy:onJobIdCopySucces"), {
        variant: "success",
      });
    } catch (e) {
      enqueueErrorSnackbar(
        enqueueSnackbar,
        t("singlestudy:onJobIdCopyError"),
        e as AxiosError
      );
    }
  };

  return (
    <Box
      sx={{
        width: "100%",
        height: "calc(0px + 100%)",
        display: "flex",
        justifyContent: jobs.length > 0 ? "flex-start" : "center",
        alignItems: jobs.length > 0 ? "flex-start" : "center",
        overflowX: "hidden",
        overflowY: "auto",
        ...scrollbarStyle,
      }}
    >
      <Stepper
        activeStep={-1}
        orientation="vertical"
        connector={<QontoConnector />}
        sx={{ width: "100%", px: 2 }}
      >
        {jobs.map((job, index) => (
          <Step key={job.id}>
            <StepLabel
              StepIconComponent={({ className }: StepIconProps) =>
                QontoStepIcon({ className, status: job.status })
              }
            >
              <Box
                width="100%"
                height="60px"
                pt={2}
                display="flex"
                flexDirection="column"
                justifyContent="flex-start"
              >
                <Box
                  width="100%"
                  height="30px"
                  display="flex"
                  justifyContent="flex-start"
                >
                  {moment(convertUTCToLocalTime(job.creationDate)).format(
                    "ddd, MMM D YYYY, HH:mm:ss"
                  )}
                  {job.completionDate &&
                    ` => ${moment(
                      convertUTCToLocalTime(job.completionDate)
                    ).format("ddd, MMM D YYYY, HH:mm:ss")}`}
                </Box>
                <Box
                  width="100%"
                  height="30px"
                  display="flex"
                  justifyContent="flex-start"
                >
                  {job.outputId}
                </Box>
                <Box
                  width="100%"
                  height="30px"
                  display="flex"
                  justifyContent="flex-start"
                  py={1}
                >
                  <Tooltip title={t("singlestudy:copyJobId") as string}>
                    <ContentCopyIcon
                      onClick={() => copyId(job.id)}
                      sx={{
                        mx: 0.5,
                        cursor: "pointer",
                        width: 20,
                        height: 20,
                        "&:hover": {
                          color: "secondary.dark",
                        },
                      }}
                    />
                  </Tooltip>
                  <Tooltip title={t("singlestudy:taskLog") as string}>
                    <DescriptionIcon
                      sx={{
                        mx: 0.5,
                        cursor: "pointer",
                        width: 20,
                        height: 20,
                        "&:hover": {
                          color: "secondary.dark",
                        },
                      }}
                    />
                  </Tooltip>
                  <Tooltip title={t("singlestudy:taskErrorLog") as string}>
                    <InfoIcon
                      sx={{
                        cursor: "pointer",
                        width: 20,
                        height: 20,
                        "&:hover": {
                          color: "secondary.dark",
                        },
                      }}
                    />
                  </Tooltip>
                  {job.status === "running" && (
                    <Box
                      flexGrow={1}
                      height="30px"
                      display="flex"
                      alignItems="center"
                      justifyContent="flex-end"
                      py={1}
                    >
                      <Tooltip title={t("singlestudy:killStudy") as string}>
                        <CancelIcon
                          onClick={() => openConfirmModal(job.id)}
                          sx={{
                            mx: 0.5,
                            cursor: "pointer",
                            "&:hover": {
                              color: "error.main",
                            },
                          }}
                        />
                      </Tooltip>
                    </Box>
                  )}
                </Box>
              </Box>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
      {openConfirmationModal && (
        <ConfirmationModal
          open={openConfirmationModal}
          message={t("singlestudy:confirmKill")}
          handleYes={() => killTask(jobIdKill as string)}
          handleNo={() => setOpenConfirmationModal(false)}
        />
      )}
    </Box>
  );
}
