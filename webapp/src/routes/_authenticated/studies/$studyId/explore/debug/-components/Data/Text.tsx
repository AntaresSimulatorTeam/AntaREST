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
import { getRawFile } from "@/services/api/studies/raw";
import { getStudyData } from "@/services/api/study";
import { downloadFile } from "@/utils/fileUtils";
import GridOffIcon from "@mui/icons-material/GridOff";
import { useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Light as SyntaxHighlighter, type SyntaxHighlighterProps } from "react-syntax-highlighter";
import ini from "react-syntax-highlighter/dist/esm/languages/hljs/ini";
import plaintext from "react-syntax-highlighter/dist/esm/languages/hljs/plaintext";
import properties from "react-syntax-highlighter/dist/esm/languages/hljs/properties";
import xml from "react-syntax-highlighter/dist/esm/languages/hljs/xml";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { isEmptyContent, parseContent, type DataCompProps } from "../../-utils";
import { Filename, Menubar } from "./styles";

SyntaxHighlighter.registerLanguage("xml", xml);
SyntaxHighlighter.registerLanguage("plaintext", plaintext);
SyntaxHighlighter.registerLanguage("ini", ini);
SyntaxHighlighter.registerLanguage("properties", properties);

// Ex: "[2024-05-21 17:18:57][solver][check]"
const logsRegex = /^(\[[^\]]*\]){3}/;
// Ex: "EXP : 0"
const propertiesRegex = /^[^:]+ : [^:]+/;

function getSyntaxProps(data: string | string[]): SyntaxHighlighterProps {
  const isArray = Array.isArray(data);
  const text = isArray ? data.join("\n") : data;

  return {
    children: text,
    showLineNumbers: isArray,
    language: (() => {
      const firstLine = text.split("\n")[0];
      if (firstLine.startsWith("<?xml")) {
        return "xml";
      } else if (logsRegex.test(firstLine)) {
        return "ini";
      } else if (propertiesRegex.test(firstLine)) {
        return "properties";
      }
      return "plaintext";
    })(),
  };
}

function Text({ studyId, filePath, filename, fileType, canEdit }: DataCompProps) {
  const { t } = useTranslation();
  const theme = useTheme();

  const textRes = usePromiseWithSnackbarError(
    () =>
      getStudyData<string>(studyId, filePath).then((text) =>
        parseContent(text, { filePath, fileType }),
      ),
    {
      errorMessage: t("studies.error.retrieveData"),
      deps: [studyId, filePath, fileType],
    },
  );

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleDownload = async () => {
    const file = await getRawFile({ studyId, path: filePath });
    downloadFile(file, file.name);
  };

  const handleUploadSuccessful = () => {
    textRes.reload();
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <UsePromiseCond
      response={textRes}
      ifFulfilled={(text) => (
        <>
          <Menubar>
            <Filename>{filename}</Filename>
            {canEdit && (
              <UploadFileButton
                studyId={studyId}
                path={filePath}
                accept={{ "text/plain": [".txt"] }}
                onUploadSuccessful={handleUploadSuccessful}
              />
            )}
            <DownloadButton onClick={handleDownload} />
          </Menubar>
          {isEmptyContent(text) ? ( // TODO remove when files become editable
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
              {...getSyntaxProps(text)}
            />
          )}
        </>
      )}
    />
  );
}

export default Text;
