export interface NodeClickConfig {
    id: string;
    x: number;
    y: number;
    color: string;
}

export interface TestStudyConfig {
    archiveInputSeries: Array<string>;
    areas: object;
    bindings: Array<string>;
    enrModelling: string;
    outputPath: string;
    outputs: object;
    path: string;
    sets: object;
    storeNewSet: boolean;
    studyId: string;
    studyPath: string;
    version: number;
}

export interface LinkClickConfig {
    source: string;
    target: string;
}

export default {};
