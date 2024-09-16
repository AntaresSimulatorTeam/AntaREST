import { useTranslation } from "react-i18next";
import EmptyView from "../../../../../common/page/SimpleContent";
import ImageIcon from "@mui/icons-material/Image";
import { Filename, Flex, Menubar } from "./styles";
import type { DataCompProps } from "../utils";

function Image({ filename }: DataCompProps) {
  const { t } = useTranslation();

  return (
    <Flex>
      <Menubar>
        <Filename>{filename}</Filename>
      </Menubar>
      <EmptyView icon={ImageIcon} title={t("study.debug.file.image")} />
    </Flex>
  );
}

export default Image;
