import { Box, Button, Typography } from "@mui/material";
import { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useOutletContext } from "react-router-dom";
import { StudyMetadata } from "../../../../../../../common/types";
import useEnqueueErrorSnackbar from "../../../../../../../hooks/useEnqueueErrorSnackbar";
import useAppDispatch from "../../../../../../../redux/hooks/useAppDispatch";
import useAppSelector from "../../../../../../../redux/hooks/useAppSelector";
import {
  getSelectedLink,
  getSelectedNode,
} from "../../../../../../../redux/selectors";
import ConfirmationDialog from "../../../../../../common/dialogs/ConfirmationDialog";
import { AreaDeleteIcon } from "../style";

function DeleteAreaDialog() {
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const [t] = useTranslation();
  const dispatch = useAppDispatch();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<boolean>(false);
  const selectedNode = useAppSelector(getSelectedNode);
  const selectedLink = useAppSelector(getSelectedLink);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDelete = async () => {
    // Delete node
    if (selectedNode) {
      try {
        await dispatch(
          deleteMapNode({ studyId: study.id, source: selectedNode.id })
        );
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.error.deleteAreaOrLink"),
          e as AxiosError
        );
      }
    }
    // Delete link
    if (selectedLink) {
      try {
        await dispatch(
          deleteMapLink({
            studyId: study.id,
            source: selectedLink.source,
            target: selectedLink.target,
          })
        );
      } catch (e) {
        enqueueErrorSnackbar(
          t("study.error.deleteAreaOrLink"),
          e as AxiosError
        );
      }
    }
    setOpenConfirmationModal(false);
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
            dispatch(setSelectedNode(undefined));
            dispatch(setSelectedLink(undefined));
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
            {selectedNode && t("study.question.deleteArea")}
            {selectedLink && t("study.question.deleteLink")}
          </Typography>
        </ConfirmationDialog>
      )}
    </>
  );
}

export default DeleteAreaDialog;
