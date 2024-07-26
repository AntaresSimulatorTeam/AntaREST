import { useTranslation } from "react-i18next";
import LiveHelpRoundedIcon from "@mui/icons-material/LiveHelpRounded";
import { Box } from "@mui/material";
import { SvgIconComponent } from "@mui/icons-material";

export interface EmptyViewProps {
  title?: string;
  icon?: SvgIconComponent;
}

function EmptyView(props: EmptyViewProps) {
  const { title, icon: Icon = LiveHelpRoundedIcon } = props;
  const { t } = useTranslation();

  return (
    <Box
      sx={{
        height: 1,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {Icon && <Icon sx={{ height: 100, width: 100 }} />}
      <div>{title || t("common.noContent")}</div>
    </Box>
  );
}

export default EmptyView;
