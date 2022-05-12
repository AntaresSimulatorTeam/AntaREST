import { Button } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import ImportStudy from "./ImportStudyDialog";
import CreateStudyDialog from "./CreateStudyDialog";

function HeaderRight() {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [t] = useTranslation();

  return (
    <>
      <Button
        variant="outlined"
        color="primary"
        startIcon={<GetAppOutlinedIcon />}
        onClick={() => setOpenImportDialog(true)}
      >
        {t("main:import")}
      </Button>
      <Button
        sx={{ ml: 2 }}
        variant="contained"
        color="primary"
        startIcon={<AddCircleOutlineOutlinedIcon />}
        onClick={() => setOpenCreateDialog(true)}
      >
        {t("main:create")}
      </Button>
      {openCreateDialog && (
        <CreateStudyDialog
          open={openCreateDialog}
          onClose={() => setOpenCreateDialog(false)}
        />
      )}
      {openImportDialog && (
        <ImportStudy
          open={openImportDialog}
          onClose={() => setOpenImportDialog(false)}
        />
      )}
    </>
  );
}

export default HeaderRight;
