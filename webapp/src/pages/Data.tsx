import { useTranslation } from "react-i18next";
import StorageIcon from "@mui/icons-material/Storage";
import RootPage from "../components/common/page/RootPage";
import UnderConstruction from "../components/common/page/UnderConstruction";

function Data() {
  const [t] = useTranslation();

  return (
    <RootPage title={t("main:data")} titleIcon={StorageIcon}>
      <UnderConstruction />
    </RootPage>
  );
}

export default Data;
