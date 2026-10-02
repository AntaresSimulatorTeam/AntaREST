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
import { getUserResourceContent } from "@/services/api/studies/userResources";
import { downloadFile } from "@/utils/fileUtils";
import BlockIcon from "@mui/icons-material/Block";
import { useTranslation } from "react-i18next";
import type { DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

function Unsupported({ studyId, path, name }: DataCompProps) {
  const { t } = useTranslation();

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async () => {
    const blob = await getUserResourceContent({ studyId, path });
    downloadFile(blob, name);
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <Menubar>
        <Filename>{name}</Filename>
        <UploadFileButton studyId={studyId} studyStorageMode="database" path={path} />
        <DownloadButton onClick={handleDownload} />
      </Menubar>
      <EmptyView icon={BlockIcon} title={t("study.fileExplorer.file.unsupported")} />
    </>
  );
}

export default Unsupported;
