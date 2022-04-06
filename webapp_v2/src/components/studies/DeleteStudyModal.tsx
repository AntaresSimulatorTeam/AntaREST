import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicModal from "../common/BasicModal";

interface Props {
  open: boolean;
  onClose: () => void;
  onYesClick: () => void;
}

export default function DeleteStudyModal(props: Props) {
  const [t] = useTranslation();
  const { open, onClose, onYesClick } = props;

  return (
    <BasicModal
      title={t("main:confirmationModalTitle")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:noButton")}
      actionButtonLabel={t("main:yesButton")}
      onActionButtonClick={onYesClick}
      rootStyle={{
        width: "600px",
        height: "200px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        width="100%"
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="center"
        p={2}
        boxSizing="border-box"
      >
        <Typography>{t("studymanager:confirmdelete")}</Typography>
      </Box>
    </BasicModal>
  );
}
