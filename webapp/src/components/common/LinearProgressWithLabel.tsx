import {
  Tooltip,
  Box,
  LinearProgress,
  Typography,
  LinearProgressProps,
} from "@mui/material";
import * as R from "ramda";

const renderLoadColor = (val: number): LinearProgressProps["color"] =>
  R.cond([
    [(v: number) => v > 90, () => "error" as const],
    [(v: number) => v > 75, () => "primary" as const],
    [R.T, () => "success" as const],
  ])(val);

interface PropsType {
  indicator: number;
  size?: string;
  tooltip: string;
  gradiant?: boolean;
}

function LinearProgressWithLabel(props: PropsType) {
  const { indicator, size = "100%", tooltip, gradiant = false } = props;

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
            indicator || 0,
          )}%`}</Typography>
        </Box>
      </Box>
    </Tooltip>
  );
}

export default LinearProgressWithLabel;
