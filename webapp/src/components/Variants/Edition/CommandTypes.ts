export interface CommandItem {
    id?: string;
    name: string;
    action: string;
    args: any;
}

export interface CreateArea {
    area_name: string;
}

export type TimeStep = 'hourly' | 'daily' | 'weekly'
export type BindingConstraintOperator = 'both' | 'equal' | 'greater' | 'less'

export interface CreateBindingConstraint {
    name: string;
    enabled: boolean;
    time_step: TimeStep;
    operator: BindingConstraintOperator;
    coeffs: {[elm: string]: Array<number>};
    values: Array<Array<number>> | Array<string>;
    comments?: string;
}

export default {};
