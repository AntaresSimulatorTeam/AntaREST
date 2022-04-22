import { useState } from "react";
import { AxiosError } from "axios";
import {
  Box,
  Typography,
  Divider,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
} from "@mui/material";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import VisibilityIcon from "@mui/icons-material/Visibility";
import DeleteIcon from "@mui/icons-material/Delete";
import useEnqueueErrorSnackbar from "../../../../hooks/useEnqueueErrorSnackbar";
// import ImportForm from "../../../common/ImportForm";
import BasicModal from "../../../common/BasicModal";
import { Title } from "./Styles";

const logErr = debug("antares:createimportform:error");

interface PropType {
  title: string;
  content: Array<string>;
  onDelete: (filename: string) => Promise<void>;
  onRead: (filename: string) => Promise<void>;
  uploadFile: (file: File) => Promise<void>;
}

function XpansionTable(props: PropType) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { title, content, onDelete, onRead, uploadFile } = props;
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<string>("");

  const onImport = async (file: File) => {
    try {
      await uploadFile(file);
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studymanager:failtosavedata"), e as AxiosError);
    } finally {
      enqueueSnackbar(t("studymanager:savedatasuccess"), {
        variant: "success",
      });
    }
  };

  console.log(onImport);

  return (
    <Box
      display="flex"
      overflow="hidden"
      width="100%"
      height="100%"
      flexDirection="column"
    >
      <Title>{title}</Title>
      <Divider sx={{ mt: 1, mb: 2 }} />
      <Box display="flex" justifyContent="flex-end">
        {/* <ImportForm text={t("main:import")} onImport={onImport} /> */}
      </Box>
      <Box
        width="100%"
        flexGrow={1}
        display="flex"
        flexDirection="column"
        alignItems="center"
        overflow="auto"
      >
        <TableContainer component={Box}>
          <Table sx={{ minWidth: "650px" }} aria-label="simple table">
            <TableHead>
              <TableRow>
                <TableCell>{t("xpansion:fileName")}</TableCell>
                <TableCell align="right">{t("xpansion:options")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {content.map((row) => (
                <TableRow key={row}>
                  <TableCell component="th" scope="row">
                    {row}
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      display: "flex",
                      flexDirection: "row",
                      justifyContent: "flex-end",
                      alignItems: "center",
                    }}
                  >
                    <VisibilityIcon
                      sx={{
                        mx: 1,
                        "&:hover": {
                          color: "secondary.main",
                          cursor: "pointer",
                        },
                      }}
                      color="primary"
                      onClick={() => onRead(row)}
                    />
                    <DeleteIcon
                      sx={{
                        mx: 1,
                        color: "error.light",
                        "&:hover": {
                          color: "error.main",
                          cursor: "pointer",
                        },
                      }}
                      color="primary"
                      onClick={() => setOpenConfirmationModal(row)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
      {openConfirmationModal && openConfirmationModal.length > 0 && (
        <BasicModal
          open={!!openConfirmationModal}
          title={t("main:confirmationModalTitle")}
          actionButtonLabel={t("main:yesButton")}
          closeButtonLabel={t("main:noButton")}
          onActionButtonClick={() => {
            onDelete(openConfirmationModal);
            setOpenConfirmationModal("");
          }}
          onClose={() => setOpenConfirmationModal("")}
          rootStyle={{
            maxWidth: "800px",
            maxHeight: "800px",
            display: "flex",
            flexFlow: "column nowrap",
            alignItems: "center",
          }}
        >
          <Typography sx={{ p: 3 }}>{t("xpansion:deleteFile")}</Typography>
        </BasicModal>
      )}
    </Box>
  );
}

export default XpansionTable;
