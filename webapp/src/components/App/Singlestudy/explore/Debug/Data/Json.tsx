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

import { getRawFile } from "@/services/api/studies/raw";
import SaveIcon from "@mui/icons-material/Save";
import { Button, Divider } from "@mui/material";
import { useSnackbar } from "notistack";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import { downloadFile } from "../../../../../../utils/fileUtils";
import DownloadButton from "../../../../../common/buttons/DownloadButton";
import UploadFileButton from "../../../../../common/buttons/UploadFileButton";
import JSONEditor, {
  type JSONApi,
  type JSONEditorProps,
  type JSONState,
} from "../../../../../common/JSONEditor";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import type { DataCompProps } from "../utils";
import { Filename, Menubar } from "./styles";

function Json({ filePath, filename, studyId, canEdit }: DataCompProps) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const jsonApiRef = useRef<JSONApi>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const jsonRes = usePromiseWithSnackbarError(() => getStudyData(studyId, filePath, -1), {
    errorMessage: t("studies.error.retrieveData"),
    deps: [studyId, filePath],
  });

  useUpdateEffect(() => {
    setIsDirty(false);
    setIsSaving(false);
  }, [jsonRes.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async () => {
    const file = await getRawFile({ studyId, path: filePath });
    downloadFile(file, file.name);
  };

  const handleSaveClick = () => {
    jsonApiRef.current?.save();
  };

  const handleSave: JSONEditorProps["onSave"] = (json) => {
    return editStudy(json, studyId, filePath);
  };

  const handleSaveSuccessful: JSONEditorProps["onSaveSuccessful"] = () => {
    enqueueSnackbar(t("studies.success.saveData"), {
      variant: "success",
    });
  };

  const handleUploadSuccessful = () => {
    jsonRes.reload();
  };

  const handleStateChange = (state: JSONState) => {
    setIsDirty(state.isDirty);
    setIsSaving(state.isSaving);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={jsonRes}
      ifFulfilled={(json) => (
        <>
          <Menubar>
            <Filename>{filename}</Filename>
            <Button
              startIcon={<SaveIcon />}
              variant="contained"
              onClick={handleSaveClick}
              disabled={!isDirty || isSaving}
              loading={isSaving}
              loadingPosition="start"
            >
              {t("global.save")}
            </Button>
            <Divider orientation="vertical" flexItem />
            {canEdit && (
              <UploadFileButton
                studyId={studyId}
                path={filePath}
                accept={{ "application/json": [".json"] }}
                onUploadSuccessful={handleUploadSuccessful}
              />
            )}
            <DownloadButton onClick={handleDownload} />
          </Menubar>
          <JSONEditor
            json={json}
            modes={["tree", "code"]}
            enableSort={false}
            enableTransform={false}
            onSave={handleSave}
            onSaveSuccessful={handleSaveSuccessful}
            sx={{ flex: 1 }}
            hideSaveButton
            apiRef={jsonApiRef}
            onStateChange={handleStateChange}
          />
        </>
      )}
    />
  );
}

export default Json;
