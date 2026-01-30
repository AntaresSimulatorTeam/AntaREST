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

import BackdropLoading from "@/components/loaders/BackdropLoading";
import ViewWrapper from "@/components/page/ViewWrapper";
import type { StudyMetadata } from "@/types/types";
import { useContext } from "react";
import {
  canEditFile,
  getEffectiveFileType,
  type DataCompProps,
  type FileInfo,
  type FileType,
} from "../../-utils";
import DebugContext from "../DebugContext";
import Folder from "./Folder";
import Json from "./Json";
import Matrix from "./Matrix";
import Text from "./Text";
import Unsupported from "./Unsupported";

interface Props extends FileInfo {
  study: StudyMetadata;
}

const componentByFileType: Record<FileType, React.ComponentType<DataCompProps>> = {
  matrix: Matrix,
  json: Json,
  text: Text,
  unsupported: Unsupported,
  folder: Folder,
} as const;

function Data({ study, ...fileInfo }: Props) {
  const { isTreeLoading } = useContext(DebugContext);
  const fileType = getEffectiveFileType(fileInfo.filePath, fileInfo.fileType);
  const DataViewer = componentByFileType[fileType];

  return (
    <ViewWrapper flex={{ gap: 1 }}>
      <DataViewer
        {...fileInfo}
        studyId={study.id}
        canEdit={canEditFile(study, fileInfo.filePath)}
      />
      <BackdropLoading open={isTreeLoading} />
    </ViewWrapper>
  );
}

export default Data;
