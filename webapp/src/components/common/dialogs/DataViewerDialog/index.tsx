/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
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

import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";

import { MatrixType } from "@/common/types";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getStudyMatrixIndex } from "@/services/api/matrix";

import EditableMatrix from "../../EditableMatrix";
import SimpleLoader from "../../loaders/SimpleLoader";
import OkDialog from "../OkDialog";

import { Code } from "./styles";

type MatrixTypeWithId = MatrixType & { id?: string };

interface Props {
  studyId?: string;
  filename: string;
  content?: string | MatrixTypeWithId;
  loading?: boolean;
  onClose: () => void;
  isMatrix?: boolean;
  readOnly?: boolean;
}

function DataViewerDialog(props: Props) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const {
    studyId,
    filename,
    content,
    onClose,
    isMatrix,
    loading,
    readOnly = true,
  } = props;

  const { data: matrixIndex } = usePromiseWithSnackbarError(
    async () => {
      if (studyId) {
        return getStudyMatrixIndex(studyId);
      }
      return undefined;
    },
    {
      errorMessage: t("matrix.error.failedToRetrieveIndex"),
      deps: [studyId],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Utils
  ////////////////////////////////////////////////////////////////

  const copyId = async (matrixId: string): Promise<void> => {
    try {
      await navigator.clipboard.writeText(matrixId);
      enqueueSnackbar(t("data.success.matrixIdCopied"), {
        variant: "success",
      });
    } catch (e) {
      enqueueSnackbar(t("data.error.copyMatrixId"), { variant: "error" });
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  const renderContent = (data: MatrixTypeWithId | string) =>
    isMatrix ? (
      <Box width="100%" height="100%" p={2}>
        <EditableMatrix
          matrix={data as MatrixType}
          matrixTime={!!matrixIndex}
          matrixIndex={matrixIndex}
          readOnly={!!readOnly}
        />
      </Box>
    ) : (
      <Code>
        <code style={{ whiteSpace: "pre" }}>{data as string}</code>
      </Code>
    );

  return (
    <OkDialog
      open
      title={
        isMatrix ? (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Typography
              sx={{ fontWeight: 500, fontSize: "1.25rem" }}
            >{`Matrix - ${filename}`}</Typography>
            {content && (content as MatrixTypeWithId).id && (
              <IconButton
                onClick={() =>
                  copyId((content as MatrixTypeWithId).id as string)
                }
                sx={{
                  ml: 1,
                  color: "action.active",
                }}
              >
                <Tooltip title={t("study.copyId") as string}>
                  <ContentCopyIcon sx={{ height: "20px", width: "20px" }} />
                </Tooltip>
              </IconButton>
            )}
          </Box>
        ) : (
          filename
        )
      }
      contentProps={{
        sx: { p: 0, height: "60vh", overflow: "hidden" },
      }}
      fullWidth
      maxWidth="lg"
      okButtonText={t("global.close")}
      onOk={onClose}
    >
      {!!loading && !content && <SimpleLoader />}
      {!!content && renderContent(content)}
    </OkDialog>
  );
}

export default DataViewerDialog;
