export interface SortElement {
    id: string;
    elm: string | (() => JSX.Element);
}

export interface SortItem {
    element: SortElement;
    status: SortStatus;
}

export type SortStatus = 'INCREASE' | 'DECREASE' | 'NONE';

export default {};
