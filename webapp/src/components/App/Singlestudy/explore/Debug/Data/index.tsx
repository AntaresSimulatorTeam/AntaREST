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

import type { StudyMetadata } from "@/common/types";
import ViewWrapper from "@/components/common/page/ViewWrapper";

import { canEditFile, DataCompProps, FileInfo, FileType } from "../utils";

import Folder from "./Folder";
import Image from "./Image";
import Json from "./Json";
import Matrix from "./Matrix";
import Text from "./Text";

interface Props extends FileInfo {
  study: StudyMetadata;
  setSelectedFile: (file: FileInfo) => void;
  reloadTreeData: () => void;
}

type DataComponent = React.ComponentType<DataCompProps>;

const componentByFileType: Record<FileType, DataComponent> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  image: Image,
  folder: Folder,
} as const;

function Data(props: Props) {
  const { study, setSelectedFile, reloadTreeData, ...fileInfo } = props;
  const { fileType, filePath } = fileInfo;
  const canEdit = canEditFile(study, filePath);
  const DataViewer = componentByFileType[fileType];

  return (
    <ViewWrapper>
      <DataViewer
        {...fileInfo}
        studyId={study.id}
        canEdit={canEdit}
        setSelectedFile={setSelectedFile}
        reloadTreeData={reloadTreeData}
      />
    </ViewWrapper>
  );
}

export default Data;
