import { Button } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import ImportStudy from "./ImportStudy";
import CreateStudyModal from "./CreateStudyModal";

function HeaderRight() {
  const [openCreateModal, setOpenCreateModal] = useState<boolean>(false);
  const [t] = useTranslation();

  return (
    <>
      <ImportStudy />
      <Button
        sx={{ ml: 2 }}
        variant="contained"
        color="primary"
        startIcon={<AddCircleOutlineOutlinedIcon />}
        onClick={() => setOpenCreateModal(true)}
      >
        {t("main:create")}
      </Button>
      {openCreateModal && (
        <CreateStudyModal
          open={openCreateModal}
          onClose={() => setOpenCreateModal(false)}
        />
      )}
    </>
  );
}

export default HeaderRight;
