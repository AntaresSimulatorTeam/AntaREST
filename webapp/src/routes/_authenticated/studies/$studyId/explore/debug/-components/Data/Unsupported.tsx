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
import EmptyView from "@/components/page/EmptyView";
import { getRawFile } from "@/services/api/studies/raw";
import { downloadFile } from "@/utils/fileUtils";
import BlockIcon from "@mui/icons-material/Block";
import { useTranslation } from "react-i18next";
import type { DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

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
