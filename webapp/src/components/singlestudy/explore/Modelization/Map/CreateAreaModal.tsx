import { useState } from "react";
import { Box, Button, TextField } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { isStringEmpty } from "../../../../../services/utils";
import BasicDialog from "../../../../common/dialogs/BasicDialog";

interface PropType {
  open: boolean;
  onClose: () => void;
  onSave: (name: string, posX: number, posY: number, color: string) => void;
}

const DEFAULT_COLOR = "rgb(230, 108, 44)";
const DEFAULT_X = 0;
const DEFAULT_Y = 0;

function CreateAreaModal(props: PropType) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const { open, onClose, onSave } = props;
  const [name, setName] = useState<string>("");

  const handleSave = (
    id: string,
    posX: number,
    posY: number,
    color: string
  ) => {
    if (!isStringEmpty(id)) {
      onSave(id, posX, posY, color);
    } else {
      enqueueSnackbar(t("global:study.error.createArea"), { variant: "error" });
    }
  };

  return (
    <BasicDialog
      title={t("global:study.modelization.map.newArea")}
      open={open}
      onClose={onClose}
      contentProps={{
        sx: { width: "auto", height: "120px", p: 2 },
      }}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global:global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={() =>
              handleSave(name, DEFAULT_X, DEFAULT_Y, DEFAULT_COLOR)
            }
          >
            {t("global:global.save")}
          </Button>
        </>
      }
    >
      <Box sx={{ m: 2 }}>
        <TextField
          sx={{ height: "40px" }}
          label={t("global:global.name")}
          variant="outlined"
          onChange={(event) => setName(event.target.value as string)}
          value={name}
          size="small"
        />
      </Box>
    </BasicDialog>
  );
}

export default CreateAreaModal;
