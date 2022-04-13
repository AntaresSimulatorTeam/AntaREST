import { useTranslation } from "react-i18next";
import AssignmentIcon from "@mui/icons-material/Assignment";
import RootPage from "../components/common/page/RootPage";

function Tasks() {
  const [t] = useTranslation();

  return (
    <RootPage title={t("main:tasks")} titleIcon={AssignmentIcon}>
      In progress
    </RootPage>
  );
}

export default Tasks;
