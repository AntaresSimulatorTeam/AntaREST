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

import type { O } from "ts-toolbelt";
import type { IdentityDTO, StudyMetadata } from "../../../common/types";
import type { TaskStatus, TaskType } from "./constants";

export type TTaskStatus = O.UnionOf<typeof TaskStatus>;

export type TTaskType = O.UnionOf<typeof TaskType>;

interface BaseTaskDTO<
  TStatus extends TTaskStatus = TTaskStatus,
  TType extends TTaskType = TTaskType,
> extends IdentityDTO<string> {
  status: TStatus;
  type?: TType;
  owner?: number;
  ref_id?: string;
  creation_date_utc: string;
  completion_date_utc?: string;
  progress?: number;
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

export type TaskDTO<
  TStatus extends TTaskStatus = TTaskStatus,
  TType extends TTaskType | undefined = undefined,
> = TType extends TTaskType
  ? O.Required<BaseTaskDTO<TStatus, TType>, "type">
  : BaseTaskDTO<TStatus>;

export interface GetTasksParams<TStatus extends TTaskStatus, TType extends TTaskType | undefined> {
  status?: TStatus[];
  type?: TType[];
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
