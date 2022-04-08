import { useTranslation } from "react-i18next";
import StorageIcon from "@mui/icons-material/Storage";
import RootPage from "../components/common/page/RootPage";

function Data() {
  const [t] = useTranslation();

  return (
    <RootPage title={t("main:data")} titleIcon={StorageIcon}>
      In progress
    </RootPage>
  );
}

export default Data;
