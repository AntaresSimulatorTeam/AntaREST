import {
  Tooltip,
  Box,
  LinearProgress,
  Typography,
  LinearProgressProps,
} from "@mui/material";
import * as R from "ramda";

interface PropsType {
  indicator: number;
  size?: string;
  tooltip: string;
  gradiant?: boolean;
}

function LinearProgressWithLabel(props: PropsType) {
  const { indicator, size, tooltip, gradiant } = props;

  const renderLoadColor = (val: number): LinearProgressProps["color"] =>
    R.cond([
      [R.lt(90), () => "error"],
      [R.lt(75), () => "primary"],
      [R.T, () => "success"],
    ])(val) as LinearProgressProps["color"];

  return (
    <Tooltip title={tooltip}>
      <Box sx={{ display: "flex", alignItems: "center", width: size }}>
        <Box sx={{ width: "100%", mr: 1 }}>
          <LinearProgress
            color={gradiant ? renderLoadColor(indicator) : "inherit"}
            variant="determinate"
            value={indicator > 100 ? 100 : indicator}
          />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">{`${Math.round(
            indicator
          )}%`}</Typography>
        </Box>
      </Box>
    </Tooltip>
  );
}

LinearProgressWithLabel.defaultProps = {
  size: "100%",
  gradiant: false,
};

export default LinearProgressWithLabel;
