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
import { useOutletContext } from "react-router-dom";
import type { AxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { Box, Paper } from "@mui/material";
import type { StudyMetadata } from "../../../../../types/types";
import useEnqueueErrorSnackbar from "../../../../../hooks/useEnqueueErrorSnackbar";
import DataViewerDialog from "../../../../common/dialogs/DataViewerDialog";
import FileTable from "../../../../common/FileTable";
import { Title } from "./share/styles";
import usePromiseWithSnackbarError from "../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../common/utils/UsePromiseCond";
import type { MatrixDataDTO } from "@/components/common/Matrix/shared/types";

interface PropTypes {
  addResource: (studyId: string, file: File) => Promise<void>;
  deleteResource: (studyId: string, filename: string) => Promise<void>;
  fetchResourceContent: (studyId: string, filename: string) => Promise<MatrixDataDTO | string>;
  listResources: (studyId: string) => Promise<string[] | undefined>;
  errorMessages?: {
    add?: string;
    delete?: string;
    fetchOne?: string;
    list?: string;
  };
  title?: string;
  isMatrix?: boolean;
}

function FileList(props: PropTypes) {
  const [t] = useTranslation();
  const { study } = useOutletContext<{ study?: StudyMetadata }>();
  const {
    addResource,
    deleteResource,
    fetchResourceContent,
    listResources,
    errorMessages,
    title,
    isMatrix = false,
  } = props;
  const [viewDialog, setViewDialog] = useState<{
    filename: string;
    content: MatrixDataDTO | string;
  }>();
  const enqueueErrorSnackbar = useEnqueueErrorSnackbar();

  const res = usePromiseWithSnackbarError(
    async () => {
      if (study) {
        return listResources(study.id);
      }
    },
    {
      errorMessage: t(errorMessages?.list || "xpansion.error.loadConfiguration"),
    },
  );

  const { data, reload } = res;

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAdd = async (file: File) => {
    if (data) {
      try {
        if (study) {
          await addResource(study.id, file);
        }
      } catch (e) {
        enqueueErrorSnackbar(t(errorMessages?.add || "xpansion.error.addFile"), e as AxiosError);
      } finally {
        reload();
      }
    }
  };

  const handleRead = async (filename: string) => {
    try {
      if (study) {
        const content = await fetchResourceContent(study.id, filename);
        setViewDialog({ filename, content });
      }
    } catch (e) {
      enqueueErrorSnackbar(t(errorMessages?.fetchOne || "xpansion.error.getFile"), e as AxiosError);
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      if (study) {
        await deleteResource(study.id, filename);
        reload();
      }
    } catch (e) {
      enqueueErrorSnackbar(
        t(errorMessages?.delete || "xpansion.error.deleteFile"),
        e as AxiosError,
      );
    }
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <UsePromiseCond
        response={res}
        ifFulfilled={(data) => (
          <Box sx={{ width: "100%", height: "100%", p: 2 }}>
            <Paper sx={{ width: "100%", height: "100%", p: 2 }}>
              <FileTable
                title={<Title>{t(title || "global.files")}</Title>}
                content={data?.map((item) => ({ id: item, name: item })) || []}
                onDelete={handleDelete}
                onRead={handleRead}
                uploadFile={handleAdd}
                allowImport
                allowDelete
              />
            </Paper>
          </Box>
        )}
      />
      {!!viewDialog && (
        <DataViewerDialog
          filename={viewDialog.filename}
          content={viewDialog.content}
          onClose={() => setViewDialog(undefined)}
          isMatrix={isMatrix}
        />
      )}
    </>
  );
}

export default FileList;
