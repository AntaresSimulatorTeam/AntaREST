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

import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import { editStudy, getStudyData } from "../../../../../../services/api/study";
import JSONEditor, { JSONEditorProps } from "../../../../../common/JSONEditor";
import usePromiseWithSnackbarError from "../../../../../../hooks/usePromiseWithSnackbarError";
import UsePromiseCond from "../../../../../common/utils/UsePromiseCond";
import type { DataCompProps } from "../utils";
import DownloadButton from "../../../../../common/buttons/DownloadButton";
import { downloadFile } from "../../../../../../utils/fileUtils";
import { useEffect, useState } from "react";
import { Filename, Flex, Menubar } from "./styles";
import UploadFileButton from "../../../../../common/buttons/UploadFileButton";

function Json({ filePath, filename, studyId, canEdit }: DataCompProps) {
  const [t] = useTranslation();
  const { enqueueSnackbar } = useSnackbar();
  const [currentJson, setCurrentJson] = useState<JSONEditorProps["json"]>();

  const res = usePromiseWithSnackbarError(
    () => getStudyData(studyId, filePath, -1),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, filePath],
    },
  );

  useEffect(() => {
    setCurrentJson(res.data);
  }, [res.data]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleSave: JSONEditorProps["onSave"] = (json) => {
    return editStudy(json, studyId, filePath);
  };

  const handleSaveSuccessful: JSONEditorProps["onSaveSuccessful"] = (json) => {
    setCurrentJson(json);

    enqueueSnackbar(t("studies.success.saveData"), {
      variant: "success",
    });
  };

  const handleDownload = () => {
    if (currentJson !== undefined) {
      downloadFile(
        JSON.stringify(currentJson, null, 2),
        filename.endsWith(".json") ? filename : `${filename}.json`,
      );
    }
  };

  const handleUploadSuccessful = () => {
    res.reload();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={res}
      ifFulfilled={(json) => (
        <Flex>
          <Menubar>
            <Filename>{filename}</Filename>
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
          />
        </Flex>
      )}
    />
  );
}

export default Json;
