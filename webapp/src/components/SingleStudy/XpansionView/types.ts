export interface XpansionSettings {
    // eslint-disable-next-line camelcase
    uc_type: string;
    master: string;
    // eslint-disable-next-line camelcase
    optimaly_gap?: number;
    // eslint-disable-next-line camelcase
    max_iteration?: number;
    // eslint-disable-next-line camelcase
    yearly_weight?: string;
    // eslint-disable-next-line camelcase
    additional_constraints?: string;
    // eslint-disable-next-line camelcase
    relaxed_optimality_gap?: number;
    // eslint-disable-next-line camelcase
    cut_type?: string;
    // eslint-disable-next-line camelcase
    ampl_solver?: string;
    // eslint-disable-next-line camelcase
    ampl_presolve?: number;
    // eslint-disable-next-line camelcase
    ampl_solve_bounds_frequency?: number;
    // eslint-disable-next-line camelcase
    relative_gap?: number;
    solver?: string;
}

export interface XpansionCandidate {
    name: string;
    link: string;
    // eslint-disable-next-line camelcase
    annual_cost_per_mw: number;
    // eslint-disable-next-line camelcase
    unit_size?: number;
    // eslint-disable-next-line camelcase
    max_units?: number;
    // eslint-disable-next-line camelcase
    max_investment?: number;
    // eslint-disable-next-line camelcase
    already_installed_capacity?: number;
    // eslint-disable-next-line camelcase
    link_profile?: string;
    // eslint-disable-next-line camelcase
    already_installed_link_profile?: string;

}

export default {};
