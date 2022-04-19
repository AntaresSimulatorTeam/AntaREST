import * as React from "react";
import Box from "@mui/material/Box";
import Stepper from "@mui/material/Stepper";
import Step from "@mui/material/Step";
import StepLabel from "@mui/material/StepLabel";
import StepContent from "@mui/material/StepContent";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import CircleOutlinedIcon from "@mui/icons-material/CircleOutlined";
import {
  StepConnector,
  stepConnectorClasses,
  StepIconProps,
  styled,
} from "@mui/material";
import moment from "moment";
import { LaunchJob } from "../../../../../common/types";
import { convertUTCToLocalTime } from "../../../../../services/utils";
import { scrollbarStyle } from "../../../../../theme";

const QontoConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${stepConnectorClasses.disabled}`]: {
    [`& .${stepConnectorClasses.line}`]: {
      height: "100px",
    },
  },
}));

const QontoStepIconRoot = styled("div")<{ ownerState: { active?: boolean } }>(
  ({ theme, ownerState }) => ({
    color: theme.palette.mode === "dark" ? theme.palette.grey[700] : "#eaeaf0",
    display: "flex",
    width: "24px",
    justifyContent: "center",
    alignItems: "center",
    ...(ownerState.active && {
      color: "#784af4",
    }),
    "& .QontoStepIcon-completedIcon": {
      color: "#784af4",
      zIndex: 1,
      fontSize: 18,
    },
    "& .QontoStepIcon-inprogress": {
      width: 16,
      height: 16,
      color: theme.palette.primary.main,
    },
  })
);

function QontoStepIcon(props: StepIconProps) {
  const { active, completed, className } = props;

  return (
    <QontoStepIconRoot ownerState={{ active }} className={className}>
      {completed ? (
        <CircleOutlinedIcon className="QontoStepIcon-completedIcon" />
      ) : (
        <CircleOutlinedIcon className="QontoStepIcon-inprogress" />
      )}
    </QontoStepIconRoot>
  );
}

interface Props {
  jobs: Array<LaunchJob>;
}

export default function VerticalLinearStepper(props: Props) {
  const { jobs } = props;
  const [activeStep, setActiveStep] = React.useState(0);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
  };

  return (
    <Box
      sx={{
        width: "100%",
        height: "calc(0px + 100%)",
        display: "flex",
        justifyContent: "flex-start",
        alignItems: "flex-start",
        overflowX: "hidden",
        overflowY: "auto",
        ...scrollbarStyle,
      }}
    >
      <Stepper
        activeStep={-1}
        orientation="vertical"
        connector={<QontoConnector />}
      >
        {jobs.map((job, index) => (
          <Step key={job.id}>
            <StepLabel
              StepIconComponent={QontoStepIcon}
              optional={<Button variant="text">Action</Button>}
            >
              {moment(convertUTCToLocalTime(job.creationDate)).format(
                "ddd, MMM D YYYY, HH:mm:ss"
              )}
            </StepLabel>
            <StepContent>
              <Typography>{job.msg}</Typography>
              <Box sx={{ mb: 2 }}>
                <div>
                  <Button
                    variant="contained"
                    onClick={handleNext}
                    sx={{ mt: 1, mr: 1 }}
                  >
                    {index === jobs.length - 1 ? "Finish" : "Continue"}
                  </Button>
                  <Button
                    disabled={index === 0}
                    onClick={handleBack}
                    sx={{ mt: 1, mr: 1 }}
                  >
                    Back
                  </Button>
                </div>
              </Box>
            </StepContent>
          </Step>
        ))}
      </Stepper>
      {activeStep === jobs.length && (
        <Paper square elevation={0} sx={{ p: 3 }}>
          <Typography>All steps completed - you&apos;re finished</Typography>
          <Button onClick={handleReset} sx={{ mt: 1, mr: 1 }}>
            Reset
          </Button>
        </Paper>
      )}
    </Box>
  );
}
