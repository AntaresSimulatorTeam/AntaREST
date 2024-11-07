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

import { O } from "ts-toolbelt";
import type { IdentityDTO, StudyMetadata } from "../../../common/types";
import { TaskStatus, TaskType } from "./constants";

export type TTaskStatus = O.UnionOf<typeof TaskStatus>;

export type TTaskType = O.UnionOf<typeof TaskType>;

export interface TaskDTO extends IdentityDTO<string> {
  status: TTaskStatus;
  type?: TTaskType;
  owner?: number;
  ref_id?: string;
  creation_date_utc: string;
  completion_date_utc?: string;
  result?: {
    success: boolean;
    message: string;
    return_value?: string;
  };
  logs?: Array<{
    id: string;
    message: string;
  }>;
}

export interface GetTasksParams {
  status?: TTaskStatus[];
  type?: TTaskType[];
  name?: string;
  studyId?: StudyMetadata["id"];
  fromCreationDateUtc?: number;
  toCreationDateUtc?: number;
  fromCompletionDateUtc?: number;
  toCompletionDateUtc?: number;
}

export interface GetTaskParams {
  id: TaskDTO["id"];
  waitForCompletion?: boolean;
  withLogs?: boolean;
  timeout?: number;
}
