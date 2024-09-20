import {
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Menu,
  MenuItem,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import DeleteIcon from "@mui/icons-material/Delete";
import {
  getFileIcon,
  getFileType,
  type TreeFolder,
  type DataCompProps,
  isFolder,
} from "../utils";
import { Fragment, useState } from "react";
import EmptyView from "../../../../../common/page/SimpleContent";
import { useTranslation } from "react-i18next";
import { Filename, Menubar } from "./styles";
import UploadFileButton from "../../../../../common/buttons/UploadFileButton";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import useConfirm from "../../../../../../hooks/useConfirm";
import { deleteFile } from "../../../../../../services/api/studies/raw";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../../../../utils/fnUtils";

function Folder(props: DataCompProps) {
  const {
    filename,
    filePath,
    treeData,
    enableImport,
    setSelectedFile,
    reloadTreeData,
    studyId,
  } = props;

  const { t } = useTranslation();
  const replaceFile = useConfirm();
  const removeFile = useConfirm();
  const [menuData, setMenuData] = useState<null | {
    anchorEl: HTMLElement;
    filePath: string;
  }>(null);
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const treeFolder = treeData as TreeFolder;
  const list = Object.entries(treeFolder);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleValidateUpload = (file: File) => {
    const childWithSameName = treeFolder[file.name];
    if (childWithSameName) {
      if (isFolder(childWithSameName)) {
        throw new Error(t("study.debug.folder.upload.error.replaceFolder"));
      }

      return replaceFile.showConfirm();
    }
  };

  const handleMenuClose = () => {
    setMenuData(null);
  };

  const handleDeleteClick = () => {
    handleMenuClose();

    removeFile.showConfirm().then((confirm) => {
      const filePath = menuData?.filePath;
      if (confirm && filePath) {
        deleteFile({ studyId, path: filePath })
          .then((res) => {
            reloadTreeData();
          })
          .catch((err) => {
            enqueueErrorSnackbar("Delete failed", toError(err));
          });
      }
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <List
        subheader={
          <ListSubheader>
            <Menubar>
              <Filename>{filename}</Filename>
              {enableImport && (
                <UploadFileButton
                  studyId={studyId}
                  path={(file) => `${filePath}/${file.name}`}
                  onUploadSuccessful={reloadTreeData}
                  validate={handleValidateUpload}
                />
              )}
            </Menubar>
          </ListSubheader>
        }
        sx={{
          height: 1,
          overflow: "auto",
          // Prevent scroll to display
          ...(list.length === 0 && {
            display: "flex",
            flexDirection: "column",
          }),
        }}
        dense
      >
        {list.length > 0 ? (
          list.map(([filename, data], index, arr) => {
            const fileType = getFileType(data);
            const Icon = getFileIcon(fileType);
            const isLast = index === arr.length - 1;

            return (
              <Fragment key={filename}>
                <ListItem
                  secondaryAction={
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={(event) => {
                        setMenuData({
                          anchorEl: event.currentTarget,
                          filePath: `${filePath}/${filename}`,
                        });
                      }}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  }
                  disablePadding
                >
                  <ListItemButton
                    onClick={() =>
                      setSelectedFile({
                        fileType,
                        filename,
                        filePath: `${filePath}/${filename}`,
                        treeData: data,
                      })
                    }
                  >
                    <ListItemIcon>
                      <Icon />
                    </ListItemIcon>
                    <ListItemText
                      title={filename}
                      primary={filename}
                      primaryTypographyProps={{
                        sx: { overflow: "hidden", textOverflow: "ellipsis" },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
                {!isLast && <Divider variant="fullWidth" />}
              </Fragment>
            );
          })
        ) : (
          <EmptyView title={t("study.debug.folder.empty")} icon={FolderIcon} />
        )}
      </List>
      {/* Items menu */}
      <Menu
        anchorEl={menuData?.anchorEl}
        open={!!menuData}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleDeleteClick}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          Delete
        </MenuItem>
      </Menu>
      {/* Confim file replacement */}
      <ConfirmationDialog
        title={t("study.debug.folder.upload.replaceFileConfirm.title")}
        confirmButtonText={t("global.replace")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={replaceFile.isPending}
        onConfirm={replaceFile.yes}
        onCancel={replaceFile.no}
      >
        {t("study.debug.folder.upload.replaceFileConfirm.message")}
      </ConfirmationDialog>
      {/* Confim file deletion */}
      <ConfirmationDialog
        titleIcon={DeleteIcon}
        confirmButtonText={t("global.delete")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={removeFile.isPending}
        onConfirm={removeFile.yes}
        onCancel={removeFile.no}
      >
        Delete the file?
      </ConfirmationDialog>
    </>
  );
}

export default Folder;
