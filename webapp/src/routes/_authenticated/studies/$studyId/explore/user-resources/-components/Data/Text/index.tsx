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
import UsePromiseCond from "@/components/utils/UsePromiseCond";
import usePromiseWithSnackbarError from "@/hooks/usePromiseWithSnackbarError";
import { getUserResourceContent } from "@/services/api/studies/userResources";
import { downloadFile, getFileExtension } from "@/utils/fileUtils";
import GridOffIcon from "@mui/icons-material/GridOff";
import { Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { DataCompProps } from "../../../-utils";
import { Filename, Menubar } from "../styles";
import { textContentSx } from "./styles";

function isEmptyContent(text: string): boolean {
  return typeof text === "string" && !text.trim();
}

function Text({ studyId, path, name }: DataCompProps) {
  const { t } = useTranslation();
  const fileExtension = getFileExtension(path);

  const textResponse = usePromiseWithSnackbarError(
    async () => {
      const blob = await getUserResourceContent({ studyId, path });
      return blob.text();
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path],
    },
  );

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={textResponse}
      ifFulfilled={(text) => (
        <>
          <Menubar>
            <Filename>{name}</Filename>
            <UploadFileButton
              studyId={studyId}
              studyStorageMode="database"
              path={path}
              accept={{ "*/*": [`.${fileExtension}`] }}
              onUploadSuccessful={textResponse.reload}
            />
            <DownloadButton onClick={() => downloadFile(text, name)} />
          </Menubar>
          {isEmptyContent(text) ? (
            <EmptyView icon={GridOffIcon} title={t("global.noData")} />
          ) : (
            <Typography component="pre" variant="body2" sx={textContentSx}>
              <code>{text}</code>
            </Typography>
          )}
        </>
      )}
    />
  );
}

export default Text;
