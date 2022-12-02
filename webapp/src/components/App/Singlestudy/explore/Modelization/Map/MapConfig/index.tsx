import { Button } from "@mui/material";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { useTranslation } from "react-i18next";
import UnderConstruction from "../../../../../../common/page/UnderConstruction";

interface Props {
  onClose: () => void;
}

function MapConfig({ onClose }: Props) {
  const [t] = useTranslation();

  return (
    <>
      <Button
        color="secondary"
        size="small"
        onClick={onClose}
        startIcon={<ArrowBackIcon color="secondary" />}
      >
        {t("button.back")}
      </Button>
      <UnderConstruction />
    </>
  );
}

export default MapConfig;
