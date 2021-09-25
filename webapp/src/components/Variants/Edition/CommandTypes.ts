export interface CommandItem {
    id?: string;
    action: string;
    updated: boolean;
    args: object;
}

export enum CommandEnum {
    CREATE_AREA = 'create_area',
    REMOVE_AREA = 'remove_area',
    CREATE_DISTRICT = 'create_district',
    REMOVE_DISTRICT = 'remove_district',
    CREATE_LINK = 'create_link',
    REMOVE_LINK = 'remove_link',
    CREATE_BINDING_CONSTRAINT = 'create_binding_constraint',
    UPDATE_BINDING_CONSTRAINT = 'update_binding_constraint',
    REMOVE_BINDING_CONSTRAINT = 'remove_binding_constraint',
    CREATE_CLUSTER = 'create_cluster',
    REMOVE_CLUSTER = 'remove_cluster',
    REPLACE_MATRIX = 'replace_matrix',
    UPDATE_CONFIG = 'update_config',
}

export default {};
