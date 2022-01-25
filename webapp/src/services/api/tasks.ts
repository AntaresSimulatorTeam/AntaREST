import { TaskDTO, TaskStatus } from '../../common/types';
import client from './client';

export const getStudyRunningTasks = async (sid: string): Promise<Array<TaskDTO>> => {
  const res = await client.post('/v1/tasks', {
    // eslint-disable-next-line @typescript-eslint/camelcase
    ref_id: sid,
    type: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export const getAllRunningTasks = async (): Promise<Array<TaskDTO>> => {
  const res = await client.post('/v1/tasks', {
    type: [TaskStatus.RUNNING, TaskStatus.PENDING],
  });
  return res.data;
};

export default {};
