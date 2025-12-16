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

import DataViewerDialog from "@/components/dialogs/DataViewerDialog";
import FileTable from "@/components/FileTable";
import type { MatrixDataDTO } from "@/components/Matrix/shared/types";
import ViewWrapper from "@/components/page/ViewWrapper";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useStudy from "@/routes/_authenticated/studies/$studyId/-hooks/useStudy";
import type { AxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import useEnqueueErrorSnackbar from "../../../../../../../../hooks/useEnqueueErrorSnackbar";
import usePromiseWithSnackbarError from "../../../../../../../../hooks/usePromiseWithSnackbarError";
import { Title } from "./styles";

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
  const study = useStudy();
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
    <ViewWrapper>
      <UsePromiseCond
        response={res}
        ifFulfilled={(data) => (
          <FileTable
            title={<Title>{t(title || "global.files")}</Title>}
            content={data?.map((item) => ({ id: item, name: item })) || []}
            onDelete={handleDelete}
            onRead={handleRead}
            uploadFile={handleAdd}
            allowImport
            allowDelete
          />
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
    </ViewWrapper>
  );
}

export default FileList;
