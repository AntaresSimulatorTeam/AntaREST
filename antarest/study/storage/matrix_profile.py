import calendar
import copy
import typing as t
from pathlib import Path

import pandas as pd


class MatrixProfile(t.NamedTuple):
    """
    Matrix profile for time series or classic tables.
    """

    cols: t.Sequence[str]
    rows: t.Sequence[str]
    stats: bool

    def handle_specific_matrices(
        self,
        df: pd.DataFrame,
        matrix_path: str,
        *,
        with_index: bool,
        with_header: bool,
    ) -> pd.DataFrame:
        if with_header:
            if Path(matrix_path).parts[1] == "links":
                cols = self.handle_links_columns(matrix_path)
            else:
                cols = self.cols
            if cols:
                df.columns = pd.Index(cols)
        rows = self.rows
        if with_index and rows:
            df.index = rows  # type: ignore
        return df

    def handle_links_columns(self, matrix_path: str) -> t.Sequence[str]:
        path_parts = Path(matrix_path).parts
        area_id_1 = path_parts[2]
        area_id_2 = path_parts[3]
        result = list(self.cols)
        for k, col in enumerate(result):
            if col == "Hurdle costs direct":
                result[k] = f"{col} ({area_id_1}->{area_id_2})"
            elif col == "Hurdle costs indirect":
                result[k] = f"{col} ({area_id_2}->{area_id_1})"
        return result


# noinspection SpellCheckingInspection
_SPECIFIC_MATRICES = {
    "input/hydro/common/capacity/creditmodulations_*": MatrixProfile(
        cols=[str(i) for i in range(101)],
        rows=["Generating Power", "Pumping Power"],
        stats=False,
    ),
    "input/hydro/common/capacity/maxpower_*": MatrixProfile(
        cols=[
            "Generating Max Power (MW)",
            "Generating Max Energy (Hours at Pmax)",
            "Pumping Max Power (MW)",
            "Pumping Max Energy (Hours at Pmax)",
        ],
        rows=[],
        stats=False,
    ),
    "input/hydro/common/capacity/reservoir_*": MatrixProfile(
        cols=["Lev Low (p.u)", "Lev Avg (p.u)", "Lev High (p.u)"],
        rows=[],
        stats=False,
    ),
    "input/hydro/common/capacity/waterValues_*": MatrixProfile(
        cols=[f"{i}%" for i in range(101)],
        rows=[],
        stats=False,
    ),
    "input/hydro/series/*/mod": MatrixProfile(cols=[], rows=[], stats=True),
    "input/hydro/series/*/ror": MatrixProfile(cols=[], rows=[], stats=True),
    "input/hydro/common/capacity/inflowPattern_*": MatrixProfile(cols=["Inflow Pattern (X)"], rows=[], stats=False),
    "input/hydro/prepro/*/energy": MatrixProfile(
        cols=["Expectation (MWh)", "Std Deviation (MWh)", "Min. (MWh)", "Max. (MWh)", "ROR Share"],
        rows=calendar.month_name[1:],
        stats=False,
    ),
    "input/thermal/prepro/*/*/modulation": MatrixProfile(
        cols=["Marginal cost modulation", "Market bid modulation", "Capacity modulation", "Min gen modulation"],
        rows=[],
        stats=False,
    ),
    "input/thermal/prepro/*/*/data": MatrixProfile(
        cols=["FO Duration", "PO Duration", "FO Rate", "PO Rate", "NPO Min", "NPO Max"],
        rows=[],
        stats=False,
    ),
    "input/reserves/*": MatrixProfile(
        cols=["Primary Res. (draft)", "Strategic Res. (draft)", "DSM", "Day Ahead"],
        rows=[],
        stats=False,
    ),
    "input/misc-gen/miscgen-*": MatrixProfile(
        cols=["CHP", "Bio Mass", "Bio Gaz", "Waste", "GeoThermal", "Other", "PSP", "ROW Balance"],
        rows=[],
        stats=False,
    ),
    "input/bindingconstraints/*": MatrixProfile(cols=["<", ">", "="], rows=[], stats=False),
    "input/links/*/*": MatrixProfile(
        cols=[
            "Capacités de transmission directes",
            "Capacités de transmission indirectes",
            "Hurdle costs direct",
            "Hurdle costs indirect",
            "Impedances",
            "Loop flow",
            "P.Shift Min",
            "P.Shift Max",
        ],
        rows=[],
        stats=False,
    ),
}

_SPECIFIC_MATRICES_820 = copy.deepcopy(_SPECIFIC_MATRICES)
_SPECIFIC_MATRICES_820["input/links/*/*"] = MatrixProfile(
    cols=[
        "Hurdle costs direct",
        "Hurdle costs indirect",
        "Impedances",
        "Loop flow",
        "P.Shift Min",
        "P.Shift Max",
    ],
    rows=[],
    stats=False,
)

_SPECIFIC_MATRICES_870 = copy.deepcopy(_SPECIFIC_MATRICES_820)
# noinspection SpellCheckingInspection
_SPECIFIC_MATRICES_870["input/bindingconstraints/*"] = MatrixProfile(cols=[], rows=[], stats=False)


def get_matrix_profiles_by_version(study_version: int) -> t.Dict[str, MatrixProfile]:
    if study_version < 820:
        return _SPECIFIC_MATRICES
    elif study_version < 870:
        return _SPECIFIC_MATRICES_820
    else:
        return _SPECIFIC_MATRICES_870
