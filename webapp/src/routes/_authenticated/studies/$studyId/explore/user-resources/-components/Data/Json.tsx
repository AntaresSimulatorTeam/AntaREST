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

import DownloadButton from "@/components/buttons/DownloadButton";
import UploadFileButton from "@/components/buttons/UploadFileButton";
import JSONEditor, {
  type JSONApi,
  type JSONEditorProps,
  type JSONState,
} from "@/components/JSONEditor";
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import useFormBlocker from "@/hooks/useFormBlocker";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import {
  createOrReplaceUserResource,
  getUserResourceContent,
} from "@/services/api/studies/userResources";
import { downloadFile } from "@/utils/fileUtils";
import SaveIcon from "@mui/icons-material/Save";
import { Button, Divider } from "@mui/material";
import { useSnackbar } from "notistack";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useUpdateEffect } from "react-use";
import type { DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

function Json({ path, name, studyId }: DataCompProps) {
  const { t } = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const jsonApiRef = useRef<JSONApi>(null);
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const jsonResponse = usePromiseWithSnackbarError(
    async () => {
      const jsonBlob = await getUserResourceContent({ studyId, path });
      const jsonText = await jsonBlob.text();
      const json = JSON.parse(jsonText);
      return { json, jsonBlob };
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path],
    },
  );

  useUpdateEffect(() => {
    setIsDirty(false);
    setIsSaving(false);
  }, [jsonResponse.data]);

  useFormBlocker({ isDirty, isSubmitting: isSaving });

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSaveClick = () => {
    jsonApiRef.current?.save();
  };

  const handleSave: JSONEditorProps["onSave"] = (json) => {
    return createOrReplaceUserResource({
      studyId,
      path,
      resourceType: "file",
      file: new File([JSON.stringify(json)], name, { type: "application/json" }),
    });
  };

  const handleSaveSuccessful: JSONEditorProps["onSaveSuccessful"] = () => {
    enqueueSnackbar(t("studies.success.saveData"), {
      variant: "success",
    });

    jsonResponse.reload();
  };

  const handleUploadSuccessful = () => {
    jsonResponse.reload();
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
      response={jsonResponse}
      ifFulfilled={({ json, jsonBlob }) => (
        <>
          <Menubar>
            <Filename>{name}</Filename>
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
            <UploadFileButton
              studyId={studyId}
              studyStorageMode="database"
              path={path}
              accept={{ "application/json": [".json"] }}
              onUploadSuccessful={handleUploadSuccessful}
            />
            <DownloadButton onClick={() => downloadFile(jsonBlob, name)} />
          </Menubar>
          <JSONEditor
            json={json}
            modes={["tree", "code"]}
            enableSort={false}
            enableTransform={false}
            onSave={handleSave}
            onSaveSuccessful={handleSaveSuccessful}
            sx={{
              flex: 1, // To show actions menu of items on small JSON
              overflow: "auto",
            }}
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
