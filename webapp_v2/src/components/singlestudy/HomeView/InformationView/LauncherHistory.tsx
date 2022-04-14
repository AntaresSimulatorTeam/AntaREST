import { Paper } from "@mui/material";
import { StudyMetadata } from "../../../../common/types";

interface Props {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

export default function LauncherHistory(props: Props) {
  const { study } = props;
  return (
    <Paper
      sx={{
        flex: 1,
        bgcolor: "rgba(36, 207, 157, 0.05)",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        boxSizing: "border-box",
        mx: 1,
        p: 2,
      }}
    >
      {study && study.name}
    </Paper>
  );
}
