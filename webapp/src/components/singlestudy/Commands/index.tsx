import { useTranslation } from "react-i18next";
import Toolbar from "@mui/material/Toolbar";
import Divider from "@mui/material/Divider";
import { Typography } from "@mui/material";
import { CommandDrawer, TitleContainer } from "./style";
import EditionView from "./Edition";

interface Props {
  open: boolean;
  onClose: () => void;
  studyId: string;
}

function CommandsDrawer(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, studyId } = props;

  return (
    <CommandDrawer
      variant="temporary"
      anchor="right"
      open={open}
      onClose={onClose}
    >
      <Toolbar sx={{ py: 3 }}>
        <TitleContainer>
          <Typography sx={{ color: "grey.500", fontSize: "0.9em" }}>
            {t("global:variants.commands").toUpperCase()}
          </Typography>
        </TitleContainer>
      </Toolbar>
      <Divider style={{ height: "1px" }} />
      <EditionView studyId={studyId} />
    </CommandDrawer>
  );
}

export default CommandsDrawer;
