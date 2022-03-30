import { ReactNode } from 'react';

export enum TaskType {
    LAUNCH = 'LAUNCH',
    EXPORT = 'EXPORT',
    VARIANT_GENERATION = 'VARIANT_GENERATION',
    COPY = 'COPY',
    ARCHIVE = 'ARCHIVE',
    UNARCHIVE = 'UNARCHIVE',
    DOWNLOAD = 'DOWNLOAD'
}

export interface JobsType {
    name: ReactNode;
    dateView: ReactNode;
    action: ReactNode;
    date: string;
    type: TaskType;
}

export default {};
