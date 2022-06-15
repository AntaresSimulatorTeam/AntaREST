import BoltIcon from "@mui/icons-material/Bolt";
import { Box, Button, IconButton, Tooltip } from "@mui/material";
import { t } from "i18next";
import { useState } from "react";
import LibraryAddCheckIcon from "@mui/icons-material/LibraryAddCheck";
import LauncherDialog from "./LauncherDialog";

interface Props {
  selectionMode: boolean;
  setSelectionMode: (active: boolean) => void;
  selectedIds: string[];
}

function BatchModeMenu(props: Props) {
  const { selectionMode, setSelectionMode, selectedIds } = props;
  const [openLaunchModal, setOpenLaunchModal] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handlerClose = () => {
    setOpenLaunchModal(false);
    setSelectionMode(false);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Box
      sx={{
        display: "flex",
        height: "100%",
        alignItems: "center",
        pr: 2,
      }}
    >
      {selectionMode && (
        <>
          <Button
            disabled={selectedIds.length === 0}
            onClick={() => setOpenLaunchModal(true)}
          >
            <BoltIcon
              sx={{
                width: "24px",
                height: "24px",
              }}
            />
            {t("global.launch")}
          </Button>
          {openLaunchModal && (
            <LauncherDialog
              open
              studyIds={selectedIds}
              onClose={handlerClose}
            />
          )}
        </>
      )}
      <Tooltip title={t("studies.batchMode") as string}>
        <IconButton
          sx={{ cursor: "pointer" }}
          color={selectionMode ? "primary" : undefined}
          onClick={() => setSelectionMode(!selectionMode)}
        >
          <LibraryAddCheckIcon />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

export default BatchModeMenu;
