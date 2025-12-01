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

import { useState } from "react";
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
import { useTranslation } from "react-i18next";
import VisibilityIcon from "@mui/icons-material/Visibility";
import UploadOutlinedIcon from "@mui/icons-material/UploadOutlined";
import DeleteIcon from "@mui/icons-material/Delete";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import DownloadIcon from "@mui/icons-material/Download";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import ConfirmationDialog from "./dialogs/ConfirmationDialog";
import type { GenericInfo } from "../../types/types";
import DownloadLink from "./DownloadLink";
import UploadDialog from "./dialogs/UploadDialog";

interface PropType {
  title: React.ReactNode;
  content: GenericInfo[];
  onDelete?: (id: string) => Promise<void>;
  onRead: (id: string) => Promise<void> | void;
  uploadFile?: (file: File) => Promise<void>;
  onFileDownload?: (id: string) => string;
  onAssign?: (id: string) => Promise<void>;
  allowImport?: boolean;
  allowDelete?: boolean;
  copyId?: boolean;
}

function FileTable(props: PropType) {
  const {
    title,
    content,
    onDelete,
    onRead,
    uploadFile,
    onFileDownload,
    onAssign,
    allowImport,
    allowDelete,
    copyId,
  } = props;
  const [t] = useTranslation();
  const [openConfirmationModal, setOpenConfirmationModal] = useState("");
  const [openUploadDialog, setOpenUploadDialog] = useState(false);

  return (
    <Box display="flex" overflow="hidden" width="100%" height="100%" flexDirection="column">
      {title}
      <Divider sx={{ mt: 1, mb: 2 }} />
      {allowImport && (
        <Box display="flex" justifyContent="flex-end">
          <Button
            variant="outlined"
            color="primary"
            startIcon={<UploadOutlinedIcon />}
            onClick={() => setOpenUploadDialog(true)}
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
                <TableCell sx={{ color: "text.secondary" }}>{t("xpansion.fileName")}</TableCell>
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
                          onClick={() => navigator.clipboard.writeText(row.id as string)}
                          sx={{
                            mx: 1,
                            color: "action.active",
                          }}
                        >
                          <Tooltip title={t("global.copyId") as string}>
                            <ContentCopyIcon sx={{ height: "20px", width: "20px" }} />
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
                        onClick={() => setOpenConfirmationModal(row.id as string)}
                        sx={{
                          color: "error.light",
                        }}
                      >
                        <Tooltip title={t("global.delete") as string}>
                          <DeleteIcon />
                        </Tooltip>
                      </IconButton>
                    )}
                    {onAssign && (
                      <IconButton
                        onClick={() => onAssign(row.id as string)}
                        sx={{
                          ml: 1,
                          color: "primary.main",
                        }}
                      >
                        <Tooltip title={t("global.assign") as string}>
                          <ArrowForwardIcon />
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
      {openConfirmationModal && onDelete && (
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
      {openUploadDialog && (
        <UploadDialog
          open={openUploadDialog}
          onCancel={() => setOpenUploadDialog(false)}
          onImport={async (file) => uploadFile?.(file)}
        />
      )}
    </Box>
  );
}

export default FileTable;
