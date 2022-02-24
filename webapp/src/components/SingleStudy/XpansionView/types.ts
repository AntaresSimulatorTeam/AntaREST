export interface XpansionSettings {
    // eslint-disable-next-line camelcase
    uc_type: string;
    master: string;
    // eslint-disable-next-line camelcase
    optimality_gap: number;
    // eslint-disable-next-line camelcase
    max_iteration?: number;
    // eslint-disable-next-line camelcase
    yearly_weight?: string;
    // eslint-disable-next-line camelcase
    'additional-constraints'?: string;
    // eslint-disable-next-line camelcase
    'relaxed-optimality-gap'?: number;
    // eslint-disable-next-line camelcase
    cut_type?: string;
    // eslint-disable-next-line camelcase
    'ampl.solver'?: string;
    // eslint-disable-next-line camelcase
    'ampl.presolve'?: number;
    // eslint-disable-next-line camelcase
    'ampl.solve_bounds_frequency'?: number;
    // eslint-disable-next-line camelcase
    relative_gap?: number;
    solver?: string;
}

export interface XpansionCandidate {
    name: string;
    link: string;
    // eslint-disable-next-line camelcase
    'annual-cost-per-mw'?: number;
    // eslint-disable-next-line camelcase
    'unit-size'?: number;
    // eslint-disable-next-line camelcase
    'max-units'?: number;
    // eslint-disable-next-line camelcase
    'max-investment'?: number;
    // eslint-disable-next-line camelcase
    'already-installed-capacity'?: number;
    // eslint-disable-next-line camelcase
    'link-profile'?: string;
    // eslint-disable-next-line camelcase
    'already-installed-link-profile'?: string;
}

export default {};
