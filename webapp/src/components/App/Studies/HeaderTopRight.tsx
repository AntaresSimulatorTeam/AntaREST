import { Button } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import { createStudy } from "../../../redux/ducks/studies";
import ImportDialog from "../../common/dialogs/ImportDialog";
import CreateStudyDialog from "./CreateStudyDialog";
import useAppDispatch from "../../../redux/hooks/useAppDispatch";

function HeaderRight() {
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openImportDialog, setOpenImportDialog] = useState(false);
  const [t] = useTranslation();
  const dispatch = useAppDispatch();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleImport = (
    file: File,
    onUploadProgress: (progress: number) => void,
  ) => {
    return dispatch(
      createStudy({
        file,
        onUploadProgress,
      }),
    ).unwrap();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Button
        variant="outlined"
        color="primary"
        startIcon={<UploadOutlinedIcon />}
        onClick={() => setOpenImportDialog(true)}
      >
        {t("global.import")}
      </Button>
      <Button
        sx={{ ml: 2 }}
        variant="contained"
        color="primary"
        startIcon={<AddCircleOutlineOutlinedIcon />}
        onClick={() => setOpenCreateDialog(true)}
      >
        {t("global.create")}
      </Button>
      {openCreateDialog && (
        <CreateStudyDialog
          open={openCreateDialog}
          onClose={() => setOpenCreateDialog(false)}
        />
      )}
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("studies.importNewStudy")}
          dropzoneText={t("studies.importHint")}
          onCancel={() => setOpenImportDialog(false)}
          onImport={handleImport}
        />
      )}
    </>
  );
}

export default HeaderRight;
