import { useTranslation } from "react-i18next";
import EmptyView from "../../../../../common/page/SimpleContent";
import ImageIcon from "@mui/icons-material/Image";

function Image() {
  const { t } = useTranslation();

  return <EmptyView icon={ImageIcon} title={t("study.debug.file.image")} />;
}

export default Image;
