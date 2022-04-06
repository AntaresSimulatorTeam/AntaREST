import { Paper } from "@mui/material";
import { StudyMetadata } from "../../../../common/types";

interface Props {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

function InformationView(props: Props) {
  return (
    <Paper
      sx={{
        width: "80%",
        height: "80%",
      }}
    />
  );
}

export default InformationView;
