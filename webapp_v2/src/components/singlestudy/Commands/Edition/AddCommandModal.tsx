import { Autocomplete, Box, TextField } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import BasicModal from "../../../common/BasicModal";
import { CommandList } from "./utils";

interface PropTypes {
  open: boolean;
  onNewCommand: (action: string) => void;
  onClose: () => void;
}

function AddCommandModal(props: PropTypes) {
  const [t] = useTranslation();
  const { open, onNewCommand, onClose } = props;
  const [action, setAction] = useState<string>(CommandList[0]);

  const onSave = async () => {
    onNewCommand(action);
    onClose();
  };

  return (
    <BasicModal
      title={t("variants:newCommand")}
      open={open}
      onClose={onClose}
      closeButtonLabel={t("main:cancelButton")}
      actionButtonLabel={t("main:create")}
      onActionButtonClick={onSave}
      rootStyle={{
        width: "600px",
        height: "500px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-start",
        alignItems: "center",
        boxSizing: "border-box",
      }}
    >
      <Box
        minWidth="100px"
        width="100%"
        height="100%"
        display="flex"
        flexDirection="column"
        justifyContent="flex-start"
        alignItems="flex-start"
        p={2}
        boxSizing="border-box"
        overflow="hidden"
      >
        <Autocomplete
          options={CommandList}
          getOptionLabel={(option) => option}
          value={action || null}
          sx={{
            width: "70%",
            height: "30px",
            boxSizing: "border-box",
            mx: 1,
            my: 2.5,
          }}
          onChange={(event, newValue: string | null) =>
            setAction(newValue !== null ? newValue : CommandList[0])
          }
          renderInput={(params) => (
            <TextField
              // eslint-disable-next-line react/jsx-props-no-spreading
              {...params}
              sx={{
                width: "100%",
                height: "30px",
                boxSizing: "border-box",
              }}
              size="small"
              label={t("variants:commandActionLabel")}
              variant="outlined"
            />
          )}
        />
      </Box>
    </BasicModal>
  );
}

export default AddCommandModal;
