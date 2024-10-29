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

import { StudyMetadata } from "@/common/types";
import { getTasks } from "@/services/api/tasks";
import { TaskStatus, TaskType } from "@/services/api/tasks/constants";
import type { TaskDTO, TTaskType } from "@/services/api/tasks/types";
import { WsChannel, WsEventType } from "@/services/webSocket/constants";
import type { WsEvent } from "@/services/webSocket/types";
import {
  addWsEventListener,
  removeWsEventListener,
  subscribeWsChannels,
  unsubscribeWsChannels,
} from "@/services/webSocket/ws";
import {
  Backdrop,
  Button,
  List,
  ListItem,
  ListItemText,
  Paper,
} from "@mui/material";
import { useEffect, useState } from "react";
import LinearProgressWithLabel from "@/components/common/LinearProgressWithLabel";
import { useTranslation } from "react-i18next";

const BLOCKING_TASK_TYPES = [
  TaskType.UpgradeStudy,
  TaskType.ThermalClusterSeriesGeneration,
] as const;

const PROGRESS_INDETERMINATE = -1;
const PROGRESS_COMPLETED = 100;

function getChannel(id: TaskDTO["id"]) {
  return WsChannel.Task + id;
}

interface BlockingTask {
  id: TaskDTO["id"];
  type: TTaskType;
  progress: number;
  error?: string;
}

interface Props {
  studyId: StudyMetadata["id"];
}

function FreezeStudy({ studyId }: Props) {
  const [blockingTasks, setBlockingTasks] = useState<BlockingTask[]>([]);
  const { t } = useTranslation();
  const hasLoadingTask = !!blockingTasks.find(
    (task) => task.progress !== PROGRESS_COMPLETED && task.error === undefined,
  );

  useEffect(() => {
    let ignore = false; // Prevent race condition

    getTasks({
      studyId,
      type: [TaskType.UpgradeStudy, TaskType.ThermalClusterSeriesGeneration],
      status: [TaskStatus.Pending, TaskStatus.Running],
    }).then((tasks) => {
      if (!ignore) {
        setBlockingTasks(
          tasks.map((task) => ({
            id: task.id,
            type: task.type!,
            progress: PROGRESS_INDETERMINATE,
          })),
        );

        subscribeWsChannels(tasks.map(({ id }) => getChannel(id)));
      }
    });

    const listener = (event: WsEvent) => {
      switch (event.type) {
        case WsEventType.TaskAdded: {
          const { id, type, study_id: taskStudyId } = event.payload;

          if (taskStudyId === studyId && BLOCKING_TASK_TYPES.includes(type)) {
            setBlockingTasks((tasks) => [
              ...tasks,
              {
                ...event.payload,
                progress: PROGRESS_INDETERMINATE,
              },
            ]);

            // For getting other events
            subscribeWsChannels(getChannel(id));
          }
          break;
        }
        case WsEventType.TsGenerationProgress: {
          setBlockingTasks((tasks) =>
            tasks.map((task) =>
              task.id === event.payload.task_id
                ? { ...task, progress: event.payload.progress }
                : task,
            ),
          );
          break;
        }
        case WsEventType.TaskFailed: {
          const { id, message } = event.payload;
          setBlockingTasks((tasks) =>
            tasks.map((task) =>
              task.id === id ? { ...task, error: message } : task,
            ),
          );
          unsubscribeWsChannels(getChannel(id));
          break;
        }
        case WsEventType.TaskCompleted: {
          const { id } = event.payload;
          setBlockingTasks((tasks) =>
            tasks.map((task) =>
              task.id === id ? { ...task, progress: PROGRESS_COMPLETED } : task,
            ),
          );
          unsubscribeWsChannels(getChannel(id));
          break;
        }
      }
    };

    addWsEventListener(listener);

    return () => {
      ignore = true;
      removeWsEventListener(listener);
      unsubscribeWsChannels();
    };
  }, [studyId]);

  return (
    <Backdrop open={blockingTasks.length > 0} sx={{ position: "absolute" }}>
      <Paper sx={{ width: 500 }}>
        <List dense>
          {blockingTasks.map(({ id, type, progress, error }) => (
            <ListItem key={id}>
              <ListItemText
                primary={
                  <LinearProgressWithLabel
                    variant={
                      progress === PROGRESS_INDETERMINATE
                        ? "indeterminate"
                        : "determinate"
                    }
                    value={progress}
                    error={error}
                  />
                }
                secondary={t(`tasks.type.${type}`)}
              />
            </ListItem>
          ))}
        </List>
        {!hasLoadingTask && (
          <Button
            sx={{ m: 1, float: "right" }}
            onClick={() => setBlockingTasks([])}
          >
            {t("global.close")}
          </Button>
        )}
      </Paper>
    </Backdrop>
  );
}

export default FreezeStudy;
