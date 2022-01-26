export interface NodeProperties {
    id: string;
    x: number;
    y: number;
    color: string;
    highlighted?: boolean;
}

export interface LinkSynthesis {
    [index: string]: object;
}

export interface AreasSynthesis {
    name: string;
    links: LinkSynthesis;
    thermals: string;
    renewables: Array<string>;
    // eslint-disable-next-line camelcase
    filters_synthesis: Array<string>;
    // eslint-disable-next-line camelcase
    filters_year: Array<string>;
}

export interface AreasNameSynthesis {
    [index: string]: AreasSynthesis;
}

export interface StudyProperties {
    archiveInputSeries: Array<string>;
    areas: AreasNameSynthesis;
    bindings: Array<string>;
    enrModelling: string;
    outputPath: string;
    outputs: string;
    path: string;
    sets: string;
    storeNewSet: boolean;
    studyId: string;
    studyPath: string;
    version: number;
}

export interface LinkProperties {
    source: string;
    target: string;
}

export interface AreaLayerColor {
    0: string;
    1: string;
    2: string;
}
export interface AreaLayerXandY {
    0: string;
    2: string;
}

export interface AreaUI {
    id: string;
    // eslint-disable-next-line camelcase
    color_b: number;
    // eslint-disable-next-line camelcase
    color_g: number;
    // eslint-disable-next-line camelcase
    color_r: number;
    layers: string;
    x: number;
    y: number;
}

export interface SingleAreaConfig {
    layerColor: AreaLayerColor;
    layerX: AreaLayerXandY;
    layerY: AreaLayerXandY;
    ui: AreaUI;
}

export interface AreasConfig {
    [index: string]: SingleAreaConfig;
}

export interface UpdateAreaUi {
    x: number;
    y: number;
    // eslint-disable-next-line camelcase
    color_rgb: Array<number>;
}

export default {};
