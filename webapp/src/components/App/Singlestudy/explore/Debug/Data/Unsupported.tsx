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
import EmptyView from "../../../../../common/page/SimpleContent";
import BlockIcon from "@mui/icons-material/Block";
import { Filename, Flex, Menubar } from "./styles";
import type { DataCompProps } from "../utils";
import DownloadButton from "@/components/common/buttons/DownloadButton";
import UploadFileButton from "@/components/common/buttons/UploadFileButton";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getStudyData } from "@/services/api/study";
import { downloadFile } from "@/utils/fileUtils";

function Unsupported({ studyId, filePath, filename, canEdit }: DataCompProps) {
  const { t } = useTranslation();

  const res = usePromiseWithSnackbarError(
    () => getStudyData<string>(studyId, filePath),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, filePath],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = () => {
    if (res.data) {
      downloadFile(res.data, filename);
    }
  };

  const handleUploadSuccessful = () => {
    res.reload();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <Flex>
      <Menubar>
        <Filename>{filename}</Filename>
        {canEdit && (
          <UploadFileButton
            studyId={studyId}
            path={filePath}
            onUploadSuccessful={handleUploadSuccessful}
          />
        )}
        <DownloadButton onClick={handleDownload} />
      </Menubar>
      <EmptyView icon={BlockIcon} title={t("study.debug.file.unsupported")} />
    </Flex>
  );
}

export default Unsupported;
