export interface SortItem {
    name: string;
    status: SortStatus;
}

export type SortStatus = 'INCREASE' | 'DECREASE' | 'NONE';

export default {};
