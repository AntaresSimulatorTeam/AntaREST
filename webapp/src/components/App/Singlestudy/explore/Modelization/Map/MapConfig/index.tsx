import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import UnderConstruction from "../../../../../../common/page/UnderConstruction";

interface Props {
  onClose: () => void;
}

function MapConfig({ onClose }: Props) {
  const [t] = useTranslation();

  return (
    <>
      <Button color="primary" size="small" onClick={onClose}>
        {t("button.back")}
      </Button>
      <UnderConstruction />
    </>
  );
}

export default MapConfig;
