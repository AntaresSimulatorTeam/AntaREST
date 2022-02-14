/*
  class XpansionSettingsDTO(BaseModel):
    optimality_gap: Optional[float] = None
    max_iteration: Optional[Union[int, Literal["inf"]]] = None
    uc_type: Union[
        Literal["expansion_fast"], Literal["expansion_accurate"]
    ] = "expansion_fast"
    master: Union[Literal["integer"], Literal["relaxed"]] = "integer"
    yearly_weight: Optional[str] = None
    additional_constraints: Optional[str] = Field(
        None, alias="additional-constraints"
    )
    relaxed_optimality_gap: Optional[float] = Field(
        None, alias="relaxed-optimality-gap"
    )
    cut_type: Optional[
        Union[Literal["average"], Literal["yearly"], Literal["weekly"]]
    ] = Field(None, alias="cut-type")
    ampl_solver: Optional[str] = Field(None, alias="ampl.solver")
    ampl_presolve: Optional[int] = Field(None, alias="ampl.presolve")
    ampl_solve_bounds_frequency: Optional[int] = Field(
        None, alias="ampl.solve_bounds_frequency"
    )
    relative_gap: Optional[float] = None
    solver: Optional[Union[Literal["Cbc"], Literal["Coin"]]] = None

  class XpansionNewCandidateDTO(BaseModel):
    name: str
    link: str
    annual_cost_per_mw: int = Field(alias="annual-cost-per-mw")
    unit_size: Optional[int] = Field(None, alias="unit-size")
    max_units: Optional[int] = Field(None, alias="max-units")
    max_investment: Optional[int] = Field(None, alias="max-investment")
    already_installed_capacity: Optional[int] = Field(
        None, alias="already-installed-capacity"
    )
    link_profile: Optional[str] = Field(None, alias="link-profile")
    already_installed_link_profile: Optional[str] = Field(
        None, alias="already-installed-link-profile"
    )
  */
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
