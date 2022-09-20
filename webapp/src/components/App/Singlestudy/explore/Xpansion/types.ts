export interface XpansionSettings {
  uc_type: string;
  master: string;
  optimality_gap: number;
  max_iteration?: number;
  "yearly-weights": string;
  "additional-constraints"?: string;
  "relaxed-optimality-gap"?: number | string;
  "cut-type"?: string;
  "ampl.solver"?: string;
  "ampl.presolve"?: number;
  "ampl.solve_bounds_frequency"?: number;
  relative_gap?: number;
  solver?: string;
  log_level?: number;
  timelimit?: number;
}

export interface XpansionCandidate {
  name: string;
  link: string;
  "annual-cost-per-mw": number;
  "unit-size"?: number;
  "max-units"?: number;
  "max-investment"?: number;
  "already-installed-capacity"?: number;
  "link-profile"?: string;
  "already-installed-link-profile"?: string;
  "direct-link-profile"?: string;
  "direct-already-installed-link-profile"?: string;
  "indirect-link-profile"?: string;
  "indirect-already-installed-link-profile"?: string;
}

export enum XpansionRenderView {
  candidate = "candidate",
  settings = "settings",
  files = "files",
  capacities = "capacities",
}

export enum XpansionResourceType {
  constraints = "constraints",
  weights = "weights",
  capacitites = "capacitites",
}

export default {};
