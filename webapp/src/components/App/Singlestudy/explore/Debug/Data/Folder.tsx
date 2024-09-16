import {
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from "@mui/material";
import FolderIcon from "@mui/icons-material/Folder";
import {
  getFileIcon,
  getFileType,
  type TreeFolder,
  type DataCompProps,
  isFolder,
} from "../utils";
import { Fragment } from "react";
import EmptyView from "../../../../../common/page/SimpleContent";
import { useTranslation } from "react-i18next";
import { Filename, Menubar } from "./styles";
import UploadFileButton from "../../../../../common/buttons/UploadFileButton";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import useConfirm from "../../../../../../hooks/useConfirm";

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
                  <ListItemText primary={filename} />
                </ListItemButton>
                {!isLast && <Divider variant="fullWidth" />}
              </Fragment>
            );
          })
        ) : (
          <EmptyView title={t("study.debug.folder.empty")} icon={FolderIcon} />
        )}
      </List>
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
    </>
  );
}

export default Folder;
