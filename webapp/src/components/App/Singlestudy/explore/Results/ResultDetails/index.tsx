import { useNavigate, useOutletContext } from "react-router";
import { useTranslation } from "react-i18next";
import { Box, Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import UnderConstruction from "../../../../../common/page/UnderConstruction";
import previewImage from "./preview.png";
import { StudyMetadata } from "../../../../../../common/types";

function ResultDetails() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const navigate = useNavigate();
  const [t] = useTranslation();

  return (
    <Box
      sx={{
        width: 1,
        height: 1,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ p: 2 }}>
        <Button
          color="inherit"
          onClick={() => navigate(`/studies/${study.id}/explore/results`)}
        >
          <ArrowBackIcon color="inherit" />
          {t("button.back")}
        </Button>
      </Box>
      <Box sx={{ flex: 1 }}>
        <UnderConstruction previewImage={previewImage} />
      </Box>
    </Box>
  );
}

export default ResultDetails;
