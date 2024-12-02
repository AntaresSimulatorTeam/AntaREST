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

import { ComponentType } from "react";
import Text from "./Text";
import Unsupported from "./Unsupported";
import Matrix from "./Matrix";
import Folder from "./Folder";
import { canEditFile, type FileInfo, type FileType } from "../utils";
import type { DataCompProps } from "../utils";
import ViewWrapper from "../../../../../common/page/ViewWrapper";
import type { StudyMetadata } from "../../../../../../common/types";
import Json from "./Json";

interface Props extends FileInfo {
  study: StudyMetadata;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

const componentByFileType: Record<FileType, ComponentType<DataCompProps>> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  unsupported: Unsupported,
  folder: Folder,
} as const;

function Data({ study, setSelectedFile, reloadTreeData, ...fileInfo }: Props) {
  const DataViewer = componentByFileType[fileInfo.fileType];

  return (
    <ViewWrapper>
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
