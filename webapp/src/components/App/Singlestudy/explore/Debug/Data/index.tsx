/** Copyright (c) 2024, RTE (https://www.rte-france.com)
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
import Json from "./Json";
import Matrix from "./Matrix";
import { FileType } from "../utils";

interface Props {
  studyId: string;
  fileType: FileType;
  filePath: string;
}

const componentByFileType = {
  matrix: Matrix,
  json: Json,
  file: Text,
} as const;

function Data({ studyId, fileType, filePath }: Props) {
  const DataViewer = componentByFileType[fileType];

  return <DataViewer studyId={studyId} path={filePath} />;
}

export default Data;
