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
import { type DataCompProps, type TreeItemInfo, type TreeItemType } from "../../-utils";
import UserResourcesContext from "../UserResourcesContext";
import Folder from "./Folder";
import Image from "./Image";
import Json from "./Json";
import Text from "./Text";
import Unsupported from "./Unsupported";

interface Props extends TreeItemInfo {
  study: StudyMetadata;
}

const componentByFileType: Record<TreeItemType, React.ComponentType<DataCompProps>> = {
  json: Json,
  text: Text,
  image: Image,
  unsupported: Unsupported,
  folder: Folder,
} as const;

function Data({ study, ...fileInfo }: Props) {
  const { isTreeLoading } = useContext(UserResourcesContext);
  const { type: fileType } = fileInfo;
  const DataViewer = componentByFileType[fileType];

  return (
    <ViewWrapper flex={{ gap: 1 }}>
      <DataViewer {...fileInfo} studyId={study.id} />
      <BackdropLoading open={isTreeLoading} />
    </ViewWrapper>
  );
}

export default Data;
