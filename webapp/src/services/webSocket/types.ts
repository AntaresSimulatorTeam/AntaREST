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

import type {
  CommandResultDTO,
  GenericInfo,
  LaunchJobDTO,
  LaunchJobProgressDTO,
  StudyMetadata,
} from "@/types/types";
import type { WsEventType } from "./constants";
import type { O } from "ts-toolbelt";
import type { FileDownloadDTO } from "../api/downloads";
import type { TaskDTO, TaskTypeValue } from "../api/tasks/types";

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

export type WsEventTypeValue = O.UnionOf<typeof WsEventType>;

////////////////////////////////////////////////////////////////
// Payloads
////////////////////////////////////////////////////////////////

export interface StudyEventPayload {
  id: string;
  name: string;
  workspace: string;
}

export interface StudyJobLogUpdateEventPayload {
  log: string;
  job_id: string;
  study_id: StudyMetadata["id"];
}

export interface TaskEventPayload {
  id: string;
  message: string;
  type: TaskTypeValue;
  study_id?: StudyMetadata["id"];
}

export interface TaskProgressEventPayload {
  task_id: TaskDTO["id"];
  progress: number;
}

////////////////////////////////////////////////////////////////
// Events
////////////////////////////////////////////////////////////////

interface StudyJobEvent {
  type:
    | typeof WsEventType.StudyJobStarted
    | typeof WsEventType.StudyJobCompleted
    | typeof WsEventType.StudyJobStatusUpdate;
  payload: LaunchJobDTO;
}

interface StudyEvent {
  type:
    | typeof WsEventType.StudyCreated
    | typeof WsEventType.StudyEdited
    | typeof WsEventType.StudyDeleted;
  payload: StudyEventPayload;
}

interface StudyDataEvent {
  type: typeof WsEventType.StudyDataEdited;
  payload: GenericInfo;
}

interface MaintenanceModeEvent {
  type: typeof WsEventType.MaintenanceMode;
  payload: boolean;
}

interface MessageInfoEvent {
  type: typeof WsEventType.MessageInfo;
  payload: string;
}

interface StudyVariantGenerationCommandResultEvent {
  type: typeof WsEventType.StudyVariantGenerationCommandResult;
  payload: CommandResultDTO;
}

interface TaskEvent {
  type:
    | typeof WsEventType.TaskAdded
    | typeof WsEventType.TaskCompleted
    | typeof WsEventType.TaskFailed;
  payload: TaskEventPayload;
}

interface StudyJobLogUpdateEvent {
  type: typeof WsEventType.StudyJobLogUpdate;
  payload: StudyJobLogUpdateEventPayload;
}

interface LaunchProgressEvent {
  type: typeof WsEventType.LaunchProgress;
  payload: LaunchJobProgressDTO;
}

interface DownloadEvent {
  type:
    | typeof WsEventType.DownloadCreated
    | typeof WsEventType.DownloadReady
    | typeof WsEventType.DownloadFailed
    | typeof WsEventType.DownloadExpired;
  payload: FileDownloadDTO;
}

interface TaskProgressEvent {
  type: typeof WsEventType.TaskProgress;
  payload: TaskProgressEventPayload;
}

export type WsEvent =
  | StudyJobEvent
  | StudyEvent
  | StudyDataEvent
  | MaintenanceModeEvent
  | MessageInfoEvent
  | StudyVariantGenerationCommandResultEvent
  | TaskEvent
  | StudyJobLogUpdateEvent
  | LaunchProgressEvent
  | DownloadEvent
  | TaskProgressEvent;

export type WsEventListener = (message: WsEvent) => void;
