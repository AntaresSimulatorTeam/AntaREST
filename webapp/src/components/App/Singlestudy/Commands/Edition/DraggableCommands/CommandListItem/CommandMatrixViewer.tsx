import { Box, Button } from "@mui/material";
import { isString } from "ramda-adjunct";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import MatrixDialog from "../../../../../Data/MatrixDialog";
import { CommandEnum, CommandItem } from "../../commandTypes";

interface PropTypes {
  command: CommandItem;
}

function CommandMatrixViewer(props: PropTypes) {
  const { command } = props;
  const { action, args } = command;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const matrixId = (args as any).matrix;
  const [openViewer, setOpenViewer] = useState(false);
  const [t] = useTranslation();

  if (action === CommandEnum.REPLACE_MATRIX && isString(matrixId)) {
    return (
      <Box sx={{ mt: 1 }}>
        <Button
          variant="text"
          onClick={() => {
            setOpenViewer((prev) => !prev);
          }}
        >
          {t("data.viewMatrix")}
        </Button>
        <MatrixDialog
          matrixInfo={{ id: matrixId, name: matrixId }}
          open={openViewer}
          onClose={() => {
            setOpenViewer(false);
          }}
        />
      </Box>
    );
  }
  return <div />;
}

export default CommandMatrixViewer;
