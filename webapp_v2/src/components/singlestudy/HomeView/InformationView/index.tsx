import { Paper, Button } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { StudyMetadata } from "../../../../common/types";

interface Props {
  // eslint-disable-next-line react/no-unused-prop-types
  study: StudyMetadata | undefined;
}

function InformationView(props: Props) {
  const { study } = props;
  const navigate = useNavigate();

  return (
    <Paper
      sx={{
        width: "80%",
        height: "80%",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      {study && (
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate(`/studies/${study.id}/explore`)}
        >
          Open
        </Button>
      )}
    </Paper>
  );
}

export default InformationView;
