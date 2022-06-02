import { ReactNode, useState } from "react";
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
  IconButton,
  Typography,
  Button,
} from "@mui/material";
import debug from "debug";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import VisibilityIcon from "@mui/icons-material/Visibility";
import GetAppOutlinedIcon from "@mui/icons-material/GetAppOutlined";
import DeleteIcon from "@mui/icons-material/Delete";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DownloadIcon from "@mui/icons-material/Download";
import useEnqueueErrorSnackbar from "../../hooks/useEnqueueErrorSnackbar";
import ConfirmationDialog from "./dialogs/ConfirmationDialog";
import { GenericInfo } from "../../common/types";
import DownloadLink from "./DownloadLink";
import ImportDialog from "./dialogs/ImportDialog";

const logErr = debug("antares:createimportform:error");

interface PropType {
  title: ReactNode;
  content: Array<GenericInfo>;
  onDelete: (id: string) => Promise<void>;
  onRead: (id: string) => Promise<void>;
  uploadFile?: (file: File) => Promise<void>;
  onFileDownload?: (id: string) => string;
  allowImport?: boolean;
  allowDelete?: boolean;
  copyId?: boolean;
}

function FileTable(props: PropType) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const {
    title,
    content,
    onDelete,
    onRead,
    uploadFile,
    onFileDownload,
    allowImport,
    allowDelete,
    copyId,
  } = props;
  const [openConfirmationModal, setOpenConfirmationModal] =
    useState<string>("");
  const [openImportDialog, setOpenImportDialog] = useState(false);

  const onImport = async (file: File) => {
    try {
      if (uploadFile) {
        await uploadFile(file);
      }
    } catch (e) {
      logErr("Failed to import file", file, e);
      enqueueErrorSnackbar(t("studies.error.saveData"), e as AxiosError);
    } finally {
      enqueueSnackbar(t("studies.success.saveData"), {
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
      {title}
      <Divider sx={{ mt: 1, mb: 2 }} />
      {allowImport && (
        <Box display="flex" justifyContent="flex-end">
          <Button
            variant="outlined"
            color="primary"
            startIcon={<GetAppOutlinedIcon />}
            onClick={() => setOpenImportDialog(true)}
          >
            {t("global.import")}
          </Button>
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
                  {t("xpansion.fileName")}
                </TableCell>
                <TableCell align="right" sx={{ color: "text.secondary" }}>
                  {t("xpansion.options")}
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {content.map((row) => (
                <TableRow
                  key={`${row.id}-${row.name}`}
                  sx={(theme) => ({
                    "&> th": {
                      padding: theme.spacing(1),
                    },
                    "&> th, >td": {
                      borderBottom: "solid 1px",
                      borderColor: theme.palette.divider,
                    },
                  })}
                >
                  <TableCell component="th" scope="row" key="name">
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      {copyId && (
                        <IconButton
                          onClick={() =>
                            navigator.clipboard.writeText(row.id as string)
                          }
                          sx={{
                            mx: 1,
                            color: "action.active",
                          }}
                        >
                          <Tooltip title={t("global.copyId") as string}>
                            <ContentCopyIcon
                              sx={{ height: "20px", width: "20px" }}
                            />
                          </Tooltip>
                        </IconButton>
                      )}
                      <Typography>{row.name}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell
                    align="right"
                    sx={{
                      display: "flex",
                      flexDirection: "row",
                      justifyContent: "flex-end",
                      alignItems: "center",
                    }}
                    key="actions"
                  >
                    <IconButton
                      onClick={() => onRead(row.id as string)}
                      sx={{
                        color: "action.active",
                      }}
                    >
                      <Tooltip title={t("global.view") as string}>
                        <VisibilityIcon />
                      </Tooltip>
                    </IconButton>
                    {onFileDownload && (
                      <DownloadLink
                        title={t("global.download") as string}
                        url={onFileDownload(row.id as string)}
                      >
                        <DownloadIcon />
                      </DownloadLink>
                    )}
                    {allowDelete && (
                      <IconButton
                        onClick={() =>
                          setOpenConfirmationModal(row.id as string)
                        }
                        sx={{
                          color: "error.light",
                        }}
                      >
                        <Tooltip title={t("global.delete") as string}>
                          <DeleteIcon />
                        </Tooltip>
                      </IconButton>
                    )}
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
          {t("xpansion.question.deleteFile")}
        </ConfirmationDialog>
      )}
      {openImportDialog && (
        <ImportDialog
          open={openImportDialog}
          title={t("global.import")}
          dropzoneText={t("global.importhint")}
          onClose={() => setOpenImportDialog(false)}
          onImport={onImport}
        />
      )}
    </Box>
  );
}

FileTable.defaultProps = {
  uploadFile: undefined,
  allowImport: false,
  allowDelete: false,
  onFileDownload: undefined,
  copyId: false,
};

export default FileTable;
