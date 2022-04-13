import { ReactNode } from 'react';
import { TaskType } from '../../common/types';

export interface JobsType {
    name: ReactNode;
    dateView: ReactNode;
    action: ReactNode;
    date: string;
    type: TaskType;
}

export default {};
