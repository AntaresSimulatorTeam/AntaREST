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
}

function LoadIndicator(props: PropsType) {
  const { indicator, size, tooltip } = props;

  const renderLoadColor = (val: number): LinearProgressProps["color"] =>
    R.cond([
      [R.lt(0.9), () => "error"],
      [R.lt(0.75), () => "primary"],
      [R.T, () => "success"],
    ])(val) as LinearProgressProps["color"];

  return (
    <Tooltip title={tooltip}>
      <Box sx={{ display: "flex", alignItems: "center", width: size }}>
        <Box sx={{ width: "100%", mr: 1 }}>
          <LinearProgress
            color={renderLoadColor(indicator)}
            variant="determinate"
            value={indicator * 100 > 100 ? 100 : indicator * 100}
          />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">{`${Math.round(
            indicator * 100
          )}%`}</Typography>
        </Box>
      </Box>
    </Tooltip>
  );
}

LoadIndicator.defaultProps = {
  size: "100%",
};

export default LoadIndicator;
