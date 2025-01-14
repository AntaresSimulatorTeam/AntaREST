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

export const WsEventType = {
  Any: "_ANY",
  StudyCreated: "STUDY_CREATED",
  StudyEdited: "STUDY_EDITED",
  StudyDeleted: "STUDY_DELETED",
  StudyDataEdited: "STUDY_DATA_EDITED",
  StudyJobStarted: "STUDY_JOB_STARTED",
  StudyJobLogUpdate: "STUDY_JOB_LOG_UPDATE",
  StudyJobCompleted: "STUDY_JOB_COMPLETED",
  StudyJobStatusUpdate: "STUDY_JOB_STATUS_UPDATE",
  StudyJobCancelRequest: "STUDY_JOB_CANCEL_REQUEST",
  StudyJobCancelled: "STUDY_JOB_CANCELLED",
  StudyVariantGenerationCommandResult: "STUDY_VARIANT_GENERATION_COMMAND_RESULT",
  TaskAdded: "TASK_ADDED",
  TaskRunning: "TASK_RUNNING",
  TaskProgress: "TASK_PROGRESS",
  TaskCompleted: "TASK_COMPLETED",
  TaskFailed: "TASK_FAILED",
  TaskCancelRequest: "TASK_CANCEL_REQUEST",
  DownloadCreated: "DOWNLOAD_CREATED",
  DownloadReady: "DOWNLOAD_READY",
  DownloadExpired: "DOWNLOAD_EXPIRED",
  DownloadFailed: "DOWNLOAD_FAILED",
  MessageInfo: "MESSAGE_INFO",
  MaintenanceMode: "MAINTENANCE_MODE",
  WorkerTask: "WORKER_TASK",
  WorkerTaskStarted: "WORKER_TASK_STARTED",
  WorkerTaskEnded: "WORKER_TASK_ENDED",
  LaunchProgress: "LAUNCH_PROGRESS",
} as const;

export const WsChannel = {
  JobStatus: "JOB_STATUS/",
  JobLogs: "JOB_LOGS/",
  Task: "TASK/",
  StudyGeneration: "GENERATION_TASK/",
} as const;
