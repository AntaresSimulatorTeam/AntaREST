import { useState } from "react";
import { AxiosError } from "axios";
import {
  Box,
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
import ImportForm from "../../../common/ImportForm";
import ConfirmationDialog from "../../../common/dialogs/ConfirmationDialog";
import { Title } from "./styles";

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

  return (
    <Box
      display="flex"
      overflow="hidden"
      width="100%"
      height="100%"
      flexDirection="column"
      sx={{ px: 1 }}
    >
      <Title>{title}</Title>
      <Divider sx={{ mt: 1, mb: 2 }} />
      <Box display="flex" justifyContent="flex-end">
        <ImportForm text={t("main:import")} onImport={onImport} />
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
              <TableRow
                sx={(theme) => ({
                  "&> th": {
                    borderBottom: `solid 1px ${theme.palette.divider}`,
                  },
                })}
              >
                <TableCell sx={{ color: "text.secondary" }}>
                  {t("xpansion:fileName")}
                </TableCell>
                <TableCell align="right" sx={{ color: "text.secondary" }}>
                  {t("xpansion:options")}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {content.map((row) => (
                <TableRow
                  key={row}
                  sx={(theme) => ({
                    "&> th, >td": {
                      borderBottom: "solid 1px",
                      borderColor: theme.palette.divider,
                    },
                  })}
                >
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
                        color: "action.active",
                        "&:hover": {
                          color: "primary.main",
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
        <ConfirmationDialog
          open
          titleIcon={DeleteIcon}
          onConfirm={() => {
            onDelete(openConfirmationModal);
            setOpenConfirmationModal("");
          }}
          onCancel={() => setOpenConfirmationModal("")}
          alert="warning"
        >
          {t("xpansion:deleteFile")}
        </ConfirmationDialog>
      )}
    </Box>
  );
}

export default XpansionTable;
