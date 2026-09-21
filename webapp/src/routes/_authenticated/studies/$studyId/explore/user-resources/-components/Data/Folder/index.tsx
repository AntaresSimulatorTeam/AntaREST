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
import { deleteUserResource } from "@/services/api/studies/userResources";
import { userResourceFolderSchema } from "@/services/api/studies/userResources/schemas";
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
  type DataCompProps,
  getTreeItemIcon,
  getTreeItemType,
  isTreeItemFolder,
} from "../../../-utils";
import UserResourcesContext from "../../UserResourcesContext";
import { Filename, Menubar } from "../styles";
import CreateFolderDialog from "./CreateFolderDialog";

function Folder({ name, path: folderPath, data, studyId }: DataCompProps) {
  const params = useParams({ from: "/_authenticated/studies/$studyId/explore/user-resources/" });
  const { reloadTree } = useContext(UserResourcesContext);
  const { t } = useTranslation();
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

  const folder = userResourceFolderSchema.parse(data);

  const fileList = [
    ...folder.directories.map((directory) => [directory.name, directory] as const),
    ...folder.files.map((filename) => [filename, filename] as const),
  ];

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleValidateUpload = (file: File) => {
    const hasFileWithSameName = folder.files.find((filename) => filename === file.name);
    if (hasFileWithSameName) {
      if (isTreeItemFolder(hasFileWithSameName)) {
        throw new Error(t("study.fileExplorer.folder.upload.error.replaceFolder"));
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
          deleteUserResource({ studyId, path: menuData.filePath })
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
              <Filename>{name}</Filename>
              <Button
                variant="contained"
                size="small"
                onClick={() => setOpenCreateFolderDialog(true)}
                startIcon={<CreateNewFolderIcon />}
              >
                {t("study.fileExplorer.folder.new")}
              </Button>
              <UploadFileButton
                studyId={studyId}
                studyStorageMode="database"
                path={(file) => (folderPath ? `${folderPath}/${file.name}` : file.name)}
                onUploadSuccessful={reloadTree}
                validate={handleValidateUpload}
              />
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
          fileList.map(([name, data], index, arr) => {
            const path = folderPath ? `${folderPath}/${name}` : name;
            const type = getTreeItemType(data);
            const Icon = getTreeItemIcon(type);
            const isNotLast = index !== arr.length - 1;

            return (
              <Fragment key={name}>
                <ListItem
                  secondaryAction={
                    <IconButton
                      edge="end"
                      onClick={(event) => {
                        setMenuData({
                          anchorEl: event.currentTarget,
                          filePath: path,
                          isFolder: type === "folder",
                          filename: name,
                        });
                      }}
                    >
                      <MoreVertIcon />
                    </IconButton>
                  }
                  disablePadding
                >
                  <RouterListItemButton
                    to="/studies/$studyId/explore/user-resources"
                    params={params}
                    search={{ path }}
                  >
                    <ListItemIcon>
                      <Icon />
                    </ListItemIcon>
                    <ListItemText
                      title={name}
                      primary={name}
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
          <EmptyView
            title={t("study.fileExplorer.folder.empty")}
            icon={getTreeItemIcon("folder")}
          />
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
        currentPath={folderPath}
      />
      {/* Confirm file replacement */}
      <ConfirmationDialog
        title={t("study.fileExplorer.folder.upload.replaceFileConfirm.title")}
        confirmButtonText={t("global.replace")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={replaceAction.isPending}
        onConfirm={replaceAction.yes}
        onCancel={replaceAction.no}
      >
        {t("study.fileExplorer.folder.upload.replaceFileConfirm.message")}
      </ConfirmationDialog>
      {/* Confirm file/folder deletion */}
      <ConfirmationDialog
        title={
          deleteAction.data?.isFolder
            ? t("study.fileExplorer.folder.deleteConfirm.title")
            : t("study.fileExplorer.file.deleteConfirm.title")
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
          ? t("study.fileExplorer.folder.deleteConfirm.message", {
              folderName: deleteAction.data?.filename,
            })
          : t("study.fileExplorer.file.deleteConfirm.message", {
              fileName: deleteAction.data?.filename,
            })}
      </ConfirmationDialog>
    </>
  );
}

export default Folder;
