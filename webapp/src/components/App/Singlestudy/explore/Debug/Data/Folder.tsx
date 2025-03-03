/**
 * Copyright (c) 2025, RTE (https://www.rte-france.com)
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
  canEditFile,
} from "../utils";
import { Fragment, useState } from "react";
import EmptyView from "../../../../../common/page/EmptyView";
import { useTranslation } from "react-i18next";
import { Filename, Menubar } from "./styles";
import UploadFileButton from "../../../../../common/buttons/UploadFileButton";
import ConfirmationDialog from "../../../../../common/dialogs/ConfirmationDialog";
import useConfirm from "../../../../../../hooks/useConfirm";
import { deleteFile } from "../../../../../../services/api/studies/raw";
import useEnqueueErrorSnackbar from "../../../../../../hooks/useEnqueueErrorSnackbar";
import { toError } from "../../../../../../utils/fnUtils";
import { useOutletContext } from "react-router";
import type { StudyMetadata } from "../../../../../../types/types";
import { useSnackbar } from "notistack";

function Folder(props: DataCompProps) {
  const { filename, filePath, treeData, canEdit, setSelectedFile, reloadTreeData, studyId } = props;

  const { t } = useTranslation();
  const { study } = useOutletContext<{ study: StudyMetadata }>();
  const replaceAction = useConfirm();
  const deleteAction = useConfirm();
  const { enqueueSnackbar } = useSnackbar();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const [menuData, setMenuData] = useState<null | {
    anchorEl: HTMLElement;
    filePath: string;
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

    deleteAction.showConfirm().then((confirm) => {
      if (confirm) {
        deleteFile({ studyId, path: menuData.filePath })
          .then(() => {
            enqueueSnackbar("wqed", { variant: "success" });
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
          <ListSubheader sx={(theme) => ({ backgroundImage: theme.vars.overlays[1] })}>
            <Menubar>
              <Filename>{filename}</Filename>
              {canEdit && (
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
                          });
                        }}
                      >
                        <MoreVertIcon />
                      </IconButton>
                    )
                  }
                  disablePadding
                >
                  <ListItemButton
                    onClick={() =>
                      setSelectedFile({
                        filename,
                        fileType: type,
                        filePath: path,
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
                      slotProps={{
                        primary: {
                          sx: { overflow: "hidden", textOverflow: "ellipsis" },
                        },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
                {isNotLast && <Divider variant="fullWidth" />}
              </Fragment>
            );
          })
        ) : (
          <EmptyView title={t("study.debug.folder.empty")} icon={FolderIcon} />
        )}
      </List>
      {/* Items menu */}
      <Menu anchorEl={menuData?.anchorEl} open={!!menuData} onClose={handleMenuClose}>
        <MenuItem onClick={handleDeleteClick}>
          <DeleteIcon sx={{ mr: 1 }} fontSize="small" />
          {t("global.delete")}
        </MenuItem>
      </Menu>
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
      {/* Confirm file deletion */}
      <ConfirmationDialog
        title={t("study.debug.file.deleteConfirm.title")}
        titleIcon={DeleteIcon}
        confirmButtonText={t("global.delete")}
        cancelButtonText={t("global.cancel")}
        maxWidth="xs"
        open={deleteAction.isPending}
        onConfirm={deleteAction.yes}
        onCancel={deleteAction.no}
      >
        {t("study.debug.file.deleteConfirm.message")}
      </ConfirmationDialog>
    </>
  );
}

export default Folder;
