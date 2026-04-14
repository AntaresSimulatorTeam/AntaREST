/**
 * Copyright (c) 2026, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import UploadFileButton from "@/components/buttons/UploadFileButton";
import ConfirmationDialog from "@/components/dialogs/ConfirmationDialog";
import EmptyView from "@/components/page/EmptyView";
import RouterListItemButton from "@/components/router/RouterListItemButton";
import useConfirm from "@/hooks/useConfirm";
import useEnqueueErrorSnackbar from "@/hooks/useEnqueueErrorSnackbar";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import { deleteFile } from "@/services/api/studies/raw";
import { toError } from "@/utils/fnUtils";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import DeleteIcon from "@mui/icons-material/Delete";
import FolderDeleteIcon from "@mui/icons-material/FolderDelete";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import {
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Menu,
  MenuItem,
} from "@mui/material";
import { useParams } from "@tanstack/react-router";
import { Fragment, useContext, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  canEditFile,
  type DataCompProps,
  getFileIcon,
  getFileType,
  isFolder,
  type TreeFolder,
} from "../../../-utils";
import DebugContext from "../../DebugContext";
import { Filename, Menubar } from "../styles";
import CreateFolderDialog from "./CreateFolderDialog";

function Folder({ filename, filePath, treeData, canEdit, studyId }: DataCompProps) {
  const params = useParams({ from: "/_authenticated/studies/$studyId/explore/debug/" });
  const { reloadTree } = useContext(DebugContext);
  const { t } = useTranslation();
  const study = useStudy();
  const replaceAction = useConfirm();
  const deleteAction = useConfirm<{ isFolder: boolean; filename: string }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();
  const [openCreateFolderDialog, setOpenCreateFolderDialog] = useState(false);

  const [menuData, setMenuData] = useState<null | {
    anchorEl: HTMLElement;
    filePath: string;
    isFolder: boolean;
    filename: string;
  }>(null);

  const treeFolder = treeData as TreeFolder;
  const fileList = Object.entries(treeFolder);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleValidateUpload = (file: File) => {
    const childWithSameName = treeFolder[file.name];
    if (childWithSameName) {
      if (isFolder(childWithSameName)) {
        throw new Error(t("study.debug.folder.upload.error.replaceFolder"));
      }

      return replaceAction.showConfirm();
    }
  };

  const handleMenuClose = () => {
    setMenuData(null);
  };

  const handleDeleteClick = () => {
    handleMenuClose();

    if (!menuData) {
      return;
    }

    deleteAction
      .showConfirm({
        data: {
          isFolder: menuData.isFolder,
          filename: menuData.filename,
        },
      })
      .then((confirm) => {
        if (confirm) {
          deleteFile({ studyId, path: menuData.filePath })
            .then(reloadTree)
            .catch((err) => {
              enqueueErrorSnackbar(t("global.error.delete"), toError(err));
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
          <ListSubheader sx={(theme) => ({ backgroundImage: theme.vars.overlays[1] })}>
            <Menubar>
              <Filename>{filename}</Filename>
              {canEdit && (
                <>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={() => setOpenCreateFolderDialog(true)}
                    startIcon={<CreateNewFolderIcon />}
                  >
                    {t("study.debug.folder.new")}
                  </Button>
                  <UploadFileButton
                    studyId={studyId}
                    path={(file) => `${filePath}/${file.name}`}
                    onUploadSuccessful={reloadTree}
                    validate={handleValidateUpload}
                  />
                </>
              )}
            </Menubar>
          </ListSubheader>
        }
        sx={[
          { overflow: "auto" },
          // Prevent scroll to display
          fileList.length === 0 && {
            display: "flex",
            flexDirection: "column",
          },
        ]}
        dense
      >
        {fileList.length > 0 ? (
          fileList.map(([filename, data], index, arr) => {
            const path = `${filePath}/${filename}`;
            const type = getFileType(data);
            const Icon = getFileIcon(type);
            const isNotLast = index !== arr.length - 1;

            return (
              <Fragment key={filename}>
                <ListItem
                  secondaryAction={
                    canEditFile(study, path) && (
                      <IconButton
                        edge="end"
                        onClick={(event) => {
                          setMenuData({
                            anchorEl: event.currentTarget,
                            filePath: path,
                            isFolder: type === "folder",
                            filename,
                          });
                        }}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    )
                  }
                  disablePadding
                >
                  <RouterListItemButton
                    to="/studies/$studyId/explore/debug"
                    params={params}
                    search={{ path }}
                  >
                    <ListItemIcon>
                      <Icon />
                    </ListItemIcon>
                    <ListItemText
                      title={filename}
                      primary={filename}
                      slotProps={{
                        primary: {
                          sx: { overflow: "hidden", textOverflow: "ellipsis" },
                        },
                      }}
                    />
                  </RouterListItemButton>
                </ListItem>
                {isNotLast && <Divider variant="fullWidth" />}
              </Fragment>
            );
          })
        ) : (
          <EmptyView title={t("study.debug.folder.empty")} icon={getFileIcon("folder")} />
        )}
      </List>
      {/* Items menu */}
      <Menu anchorEl={menuData?.anchorEl} open={!!menuData} onClose={handleMenuClose}>
        <MenuItem onClick={handleDeleteClick} dense>
          <ListItemIcon>
            <DeleteIcon color="error" />
          </ListItemIcon>
          <ListItemText slotProps={{ primary: { color: "error" } }}>
            {t("global.delete")}
          </ListItemText>
        </MenuItem>
      </Menu>
      <CreateFolderDialog
        open={openCreateFolderDialog}
        onCancel={() => setOpenCreateFolderDialog(false)}
        studyId={studyId}
        parentPath={filePath}
      />
      {/* Confirm file replacement */}
      <ConfirmationDialog
        title={t("study.debug.folder.upload.replaceFileConfirm.title")}
        confirmButtonText={t("global.replace")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={replaceAction.isPending}
        onConfirm={replaceAction.yes}
        onCancel={replaceAction.no}
      >
        {t("study.debug.folder.upload.replaceFileConfirm.message")}
      </ConfirmationDialog>
      {/* Confirm file/folder deletion */}
      <ConfirmationDialog
        title={
          deleteAction.data?.isFolder
            ? t("study.debug.folder.deleteConfirm.title")
            : t("study.debug.file.deleteConfirm.title")
        }
        titleIcon={deleteAction.data?.isFolder ? FolderDeleteIcon : DeleteIcon}
        confirmButtonText={t("global.delete")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={deleteAction.isPending}
        onConfirm={deleteAction.yes}
        onCancel={deleteAction.no}
      >
        {deleteAction.data?.isFolder
          ? t("study.debug.folder.deleteConfirm.message", {
              folderName: deleteAction.data?.filename,
            })
          : t("study.debug.file.deleteConfirm.message", { fileName: deleteAction.data?.filename })}
      </ConfirmationDialog>
    </>
  );
}

export default Folder;
