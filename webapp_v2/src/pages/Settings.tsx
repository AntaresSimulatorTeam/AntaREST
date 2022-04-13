import SettingsIcon from "@mui/icons-material/Settings";
import { useTranslation } from "react-i18next";
import RootPage from "../components/common/page/RootPage";

function Settings() {
  const [t] = useTranslation();

  return (
    <RootPage title={t("main:settings")} titleIcon={SettingsIcon}>
      In progress
    </RootPage>
  );
}

export default Settings;
