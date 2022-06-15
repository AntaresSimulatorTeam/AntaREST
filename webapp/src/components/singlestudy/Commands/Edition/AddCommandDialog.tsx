import { Autocomplete, Box, Button, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import BasicDialog from "../../../common/dialogs/BasicDialog";
import { CommandList } from "./utils";

interface PropTypes {
  open: boolean;
  onNewCommand: (action: string) => void;
  onClose: () => void;
}

function AddCommandDialog(props: PropTypes) {
  const [t] = useTranslation();
  const { open, onNewCommand, onClose } = props;
  const [action, setAction] = useState<string>(CommandList[0]);

  const onSave = async () => {
    onNewCommand(action);
    onClose();
  };

  return (
    <BasicDialog
      open={open}
      onClose={onClose}
      title={t("variants.newCommand")}
      actions={
        <>
          <Button variant="text" color="primary" onClick={onClose}>
            {t("global.cancel")}
          </Button>
          <Button
            sx={{ mx: 2 }}
            color="primary"
            variant="contained"
            onClick={onSave}
          >
            {t("global.create")}
          </Button>
        </>
      }
    >
      <Box
        sx={{
          width: "400px",
          height: "100px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          boxSizing: "border-box",
        }}
      >
        <Autocomplete
          options={CommandList}
          getOptionLabel={(option) => option}
          value={action || null}
          onChange={(event, newValue: string | null) =>
            setAction(newValue !== null ? newValue : CommandList[0])
          }
          sx={{
            width: "70%",
          }}
          renderInput={(params) => (
            <TextField
              // eslint-disable-next-line react/jsx-props-no-spreading
              {...params}
              sx={{
                width: "100%",
                height: "30px",
                m: 0,
                boxSizing: "border-box",
              }}
              size="small"
              label={t("variants.commandActionLabel")}
              variant="outlined"
            />
          )}
        />
      </Box>
    </BasicDialog>
  );
}

export default AddCommandDialog;
