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

import Text from "./Text";
import Unsupported from "./Unsupported";
import Matrix from "./Matrix";
import Folder from "./Folder";
import {
  canEditFile,
  getEffectiveFileType,
  type FileInfo,
  type FileType,
  type DataCompProps,
} from "../utils";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import type { StudyMetadata } from "../../../../../../types/types";
import Json from "./Json";

interface Props extends FileInfo {
  study: StudyMetadata;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

const componentByFileType: Record<FileType, React.ComponentType<DataCompProps>> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  unsupported: Unsupported,
  folder: Folder,
} as const;

function Data({ study, setSelectedFile, reloadTreeData, ...fileInfo }: Props) {
  const fileType = getEffectiveFileType(fileInfo.filePath, fileInfo.fileType);
  const DataViewer = componentByFileType[fileType];

  return (
    <ViewWrapper flex={{ gap: 1 }}>
      <DataViewer
        {...fileInfo}
        studyId={study.id}
        canEdit={canEditFile(study, fileInfo.filePath)}
        setSelectedFile={setSelectedFile}
        reloadTreeData={reloadTreeData}
      />
    </ViewWrapper>
  );
}

export default Data;
