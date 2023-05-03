import { Button, Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import BasicDialog, {
  BasicDialogProps,
} from "../../../../../../common/dialogs/BasicDialog";
import HydroMatrix from "./HydroMatrix";
import { HydroMatrixType } from "./utils";

interface HydroMatrixDialogProps {
  open: boolean;
  onClose: () => void;
  type: HydroMatrixType;
}

function HydroMatrixDialog({ open, onClose, type }: HydroMatrixDialogProps) {
  const { t } = useTranslation();
  const dialogProps: BasicDialogProps = {
    open,
    onClose,
    actions: (
      <Button onClick={onClose} color="primary" variant="outlined">
        {t("button.close")}
      </Button>
    ),
  };

  return (
    <BasicDialog
      {...dialogProps}
      contentProps={{
        sx: { p: 0, height: "90vh" },
      }}
      fullWidth
      maxWidth="xl"
    >
      <Box sx={{ width: 1, height: 1, p: 2 }}>
        <HydroMatrix type={type} />
      </Box>
    </BasicDialog>
  );
}

export default HydroMatrixDialog;
