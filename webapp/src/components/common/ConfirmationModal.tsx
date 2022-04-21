import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicModal from "./BasicModal";

interface Props {
  open: boolean;
  message: string;
  handleNo: () => void;
  handleYes: () => void;
}

export default function ConfirmationModal(props: Props) {
  const [t] = useTranslation();
  const { open, message, handleNo, handleYes } = props;

  return (
    <BasicModal
      title={t("main:confirmationModalTitle")}
      open={open}
      onClose={handleNo}
      closeButtonLabel={t("main:noButton")}
      actionButtonLabel={t("main:yesButton")}
      onActionButtonClick={handleYes}
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
        <Typography>{message}</Typography>
      </Box>
    </BasicModal>
  );
}
