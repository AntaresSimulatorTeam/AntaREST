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

import type {
  CommandResultDTO,
  GenericInfo,
  LaunchJobDTO,
  LaunchJobProgressDTO,
  StudyMetadata,
} from "@/common/types";
import { WsEventType } from "./constants";
import { O } from "ts-toolbelt";
import { FileDownloadDTO } from "../api/downloads";

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

export type TWsEventType = O.UnionOf<typeof WsEventType>;

////////////////////////////////////////////////////////////////
// Payloads
////////////////////////////////////////////////////////////////

export interface StudyPayload {
  id: string;
  name: string;
  workspace: string;
}

export interface StudyJobLogUpdatePayload {
  log: string;
  job_id: string;
  study_id: StudyMetadata["id"];
}

export interface TaskEventPayload {
  id: string;
  message: string;
}

////////////////////////////////////////////////////////////////
// Event
////////////////////////////////////////////////////////////////

export type WsEvent =
  | {
      type:
        | typeof WsEventType.StudyJobStarted
        | typeof WsEventType.StudyJobCompleted
        | typeof WsEventType.StudyJobStatusUpdate;
      payload: LaunchJobDTO;
    }
  | {
      type:
        | typeof WsEventType.StudyCreated
        | typeof WsEventType.StudyEdited
        | typeof WsEventType.StudyDeleted;
      payload: StudyPayload;
    }
  | {
      type: typeof WsEventType.StudyDataEdited;
      payload: GenericInfo;
    }
  | {
      type: typeof WsEventType.MaintenanceMode;
      payload: boolean;
    }
  | {
      type: typeof WsEventType.MessageInfo;
      payload: string;
    }
  | {
      type: typeof WsEventType.StudyVariantGenerationCommandResult;
      payload: CommandResultDTO;
    }
  | {
      type:
        | typeof WsEventType.TaskAdded
        | typeof WsEventType.TaskCompleted
        | typeof WsEventType.TaskFailed;
      payload: TaskEventPayload;
    }
  | {
      type: typeof WsEventType.StudyJobLogUpdate;
      payload: StudyJobLogUpdatePayload;
    }
  | {
      type: typeof WsEventType.LaunchProgress;
      payload: LaunchJobProgressDTO;
    }
  | {
      type:
        | typeof WsEventType.DownloadCreated
        | typeof WsEventType.DownloadReady
        | typeof WsEventType.DownloadFailed
        | typeof WsEventType.DownloadExpired;
      payload: FileDownloadDTO;
    };

export type WsEventListener = (message: WsEvent) => void;
