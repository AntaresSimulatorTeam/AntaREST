import { useTranslation } from "react-i18next";
import EmptyView from "../../../../../common/page/SimpleContent";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import ImageIcon from "@mui/icons-material/Image";

function Image() {
  const { t } = useTranslation();

  return (
    <ViewWrapper>
      <EmptyView icon={ImageIcon} title={t("study.debug.file.image")} />
    </ViewWrapper>
  );
}

export default Image;
