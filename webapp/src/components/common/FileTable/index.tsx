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
  Tooltip,
} from "@mui/material";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import DeleteIcon from "@mui/icons-material/Delete";
import useEnqueueErrorSnackbar from "../../../hooks/useEnqueueErrorSnackbar";
import ImportForm from "../ImportForm";
import ConfirmationDialog from "../dialogs/ConfirmationDialog";
import { Title, StyledVisibilityIcon, StyledDeleteIcon } from "./styles";
import { GenericInfo } from "../../../common/types";

const logErr = debug("antares:createimportform:error");

interface PropType {
  title: string;
  content: Array<GenericInfo>;
  onDelete: (id: string) => Promise<void>;
  onRead: (id: string) => Promise<void>;
  uploadFile?: (file: File) => Promise<void>;
  allowImport?: boolean;
}

function FileTable(props: PropType) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const { title, content, onDelete, onRead, uploadFile, allowImport } = props;
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<string>("");

  const onImport = async (file: File) => {
    try {
      if (uploadFile) {
        await uploadFile(file);
      }
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
      {allowImport && (
        <Box display="flex" justifyContent="flex-end">
          <ImportForm text={t("main:import")} onImport={onImport} />
        </Box>
      )}
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
                  key={row.id}
                  sx={(theme) => ({
                    "&> th, >td": {
                      borderBottom: "solid 1px",
                      borderColor: theme.palette.divider,
                    },
                  })}
                >
                  <TableCell component="th" scope="row">
                    {row.name}
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
                    <Tooltip
                      title="Lire"
                      onClick={() => onRead(row.id as string)}
                    >
                      <StyledVisibilityIcon />
                    </Tooltip>
                    <Tooltip
                      title="Supprimer"
                      sx={{
                        mx: 1,
                      }}
                      onClick={() => setOpenConfirmationModal(row.id as string)}
                    >
                      <StyledDeleteIcon />
                    </Tooltip>
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

FileTable.defaultProps = {
  uploadFile: undefined,
  allowImport: false,
};

export default FileTable;
