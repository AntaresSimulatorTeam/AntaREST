import { Box, Button, Typography } from "@mui/material";
import { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router";
import { StudyMetadata } from "../../../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import {
  deleteStudyMapLink,
  deleteStudyMapNode,
  StudyMapLink,
  StudyMapNode,
} from "../../../../../../../redux/ducks/studyMaps";
import {
  setCurrentArea,
  setCurrentLink,
} from "../../../../../../../redux/ducks/studySyntheses";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import { AreaDeleteIcon } from "./style";

interface Props {
  currentLink?: StudyMapLink;
  currentArea?: StudyMapNode | undefined;
}

function DeleteAreaDialog(props: Props) {
  const { currentLink, currentArea } = props;
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openConfirmationModal, setOpenConfirmationModal] = useState(false);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDelete = async () => {
    setOpenConfirmationModal(false);

    // Delete node
    if (currentArea && !currentLink) {
      try {
        await dispatch(
          deleteStudyMapNode({ studyId: study.id, nodeId: currentArea.id })
        ).unwrap();
        dispatch(setCurrentArea(""));
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.error.deleteAreaOrLink"),
          e as AxiosError
        );
      }
    }
    // Delete link
    if (currentLink && !currentArea) {
      try {
        await dispatch(
          deleteStudyMapLink({ studyId: study.id, linkId: currentLink.id })
        ).unwrap();
        dispatch(setCurrentLink(""));
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.error.deleteAreaOrLink"),
          e as AxiosError
        );
      }
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Box
        sx={{
          width: "90%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Button
          color="primary"
          size="small"
          onClick={() => {
            dispatch(setCurrentArea(""));
            dispatch(setCurrentLink(""));
          }}
        >
          {t("button.back")}
        </Button>
        <AreaDeleteIcon onClick={() => setOpenConfirmationModal(true)} />
      </Box>
      {openConfirmationModal && (
        <ConfirmationDialog
          onCancel={() => setOpenConfirmationModal(false)}
          onConfirm={handleDelete}
          alert="warning"
          open
        >
          <Typography sx={{ p: 3 }}>
            {currentArea && t("study.question.deleteArea")}
            {currentLink && t("study.question.deleteLink")}
          </Typography>
        </ConfirmationDialog>
      )}
    </>
  );
}

export default DeleteAreaDialog;
