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

import { useTranslation } from "react-i18next";
import EmptyView from "../../../../../common/page/EmptyView";
import BlockIcon from "@mui/icons-material/Block";
import { Filename, Menubar } from "./styles";
import type { DataCompProps } from "../utils";
import DownloadButton from "@/components/common/buttons/DownloadButton";
import UploadFileButton from "@/components/common/buttons/UploadFileButton";
import { downloadFile } from "@/utils/fileUtils";
import { getRawFile } from "@/services/api/studies/raw";

function Unsupported({ studyId, filePath, filename, canEdit }: DataCompProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async () => {
    const file = await getRawFile({ studyId, path: filePath });
    downloadFile(file, file.name);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Menubar>
        <Filename>{filename}</Filename>
        {canEdit && <UploadFileButton studyId={studyId} path={filePath} />}
        <DownloadButton onClick={handleDownload} />
      </Menubar>
      <EmptyView icon={BlockIcon} title={t("study.debug.file.unsupported")} />
    </>
  );
}

export default Unsupported;
