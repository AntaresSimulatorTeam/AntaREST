import { TaskDTO, TaskStatus } from "../../common/types";
import client from "./client";

export const getStudyRunningTasks = async (
  sid: string
): Promise<Array<TaskDTO>> => {
  const res = await client.post("/v1/tasks", {
    ref_id: sid,
    status: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllRunningTasks = async (): Promise<Array<TaskDTO>> => {
  const res = await client.post("/v1/tasks", {
    status: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllMiscRunningTasks = async (): Promise<Array<TaskDTO>> => {
  const res = await client.post("/v1/tasks", {
    status: [
      TaskStatus.RUNNING,
      TaskStatus.PENDING,
      TaskStatus.FAILED,
      TaskStatus.COMPLETED,
    ],
    type: ["COPY", "ARCHIVE", "UNARCHIVE", "SCAN"],
  });
  return res.data;
};

export const getTask = async (
  id: string,
  withLogs = false
): Promise<TaskDTO> => {
  const res = await client.get(`/v1/tasks/${id}?with_logs=${withLogs}`);
  return res.data;
};

export default {};
