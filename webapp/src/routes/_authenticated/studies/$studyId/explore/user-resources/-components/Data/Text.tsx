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
import { useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Light as SyntaxHighlighter, type SyntaxHighlighterProps } from "react-syntax-highlighter";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import type { DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

function getSyntaxProps(text: string, fileExtension: string): SyntaxHighlighterProps {
  const isTxtFile = fileExtension === "txt";

  return {
    children: text,
    showLineNumbers: !isTxtFile,
    language: isTxtFile ? "plaintext" : fileExtension,
  };
}

function isEmptyContent(text: string): boolean {
  return typeof text === "string" && !text.trim();
}

function Text({ studyId, path, name, type: fileType }: DataCompProps) {
  const { t } = useTranslation();
  const theme = useTheme();
  const fileExtension = getFileExtension(path);

  const textResponse = usePromiseWithSnackbarError(
    async () => {
      const blob = await getUserResourceContent({ studyId, path });
      return blob.text();
    },
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, path, fileType],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleUploadSuccessful = () => {
    textResponse.reload();
  };

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
              onUploadSuccessful={handleUploadSuccessful}
            />
            <DownloadButton onClick={() => downloadFile(text, name)} />
          </Menubar>
          {isEmptyContent(text) ? (
            <EmptyView icon={GridOffIcon} title={t("study.outputs.noData")} />
          ) : (
            <SyntaxHighlighter
              style={atomOneDark}
              lineNumberStyle={{
                opacity: 0.5,
                paddingRight: theme.spacing(3),
              }}
              customStyle={{
                margin: 0,
                padding: theme.spacing(2),
                borderRadius: theme.shape.borderRadius,
                fontSize: theme.typography.body2.fontSize,
              }}
              {...getSyntaxProps(text, fileExtension)}
            />
          )}
        </>
      )}
    />
  );
}

export default Text;
