import logging
import operator
import os
import re
import shutil
from functools import reduce
from pathlib import Path
from typing import List, Tuple, Optional, Dict, cast, Any, Callable

import numpy as np
from numpy import number
from pandas import Series, DataFrame  # type: ignore

from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    OutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.mcall import (
    OutputSimulationModeMcAll,
)

logger = logging.getLogger(__name__)

TMP_SUMMARIES_DIR = "tmp_summaries"


def _compute_stats(
    agg: Optional[Tuple[Series, Series, int]],
    el: Tuple[Series, Series, int],
) -> Tuple[Series, Series, int]:
    avg, sqr_root_std_dev, n = el
    if agg:
        agg_x, agg_mean, agg_total = agg
        return (
            agg_x.add((sqr_root_std_dev.pow(2) + avg.pow(2)).multiply(n)),
            agg_mean.add(avg.multiply(n)),
            agg_total + n,
        )
    else:
        return (
            (sqr_root_std_dev.pow(2) + avg.pow(2)).multiply(n),
            avg.multiply(n),
            n,
        )


def merge_series_stats(
    stats: List[Tuple[Series, Series, int]]
) -> Tuple[Series, Series]:
    """
    Merge statistical data (mean and square root variance)
    Args:
        stats: list of statistical data containing tuples of mean, square root variance and dataset count
    Returns:
        a tuple containing the merged mean and square root variance
    """
    e_x2, e_total, n = reduce(_compute_stats, stats, None)  # type: ignore
    sqrt_root_std_deviation = (
        e_x2.divide(n).sub(e_total.divide(n).pow(2)).pow(0.5)
    )
    mean = e_total / n
    return mean, sqrt_root_std_deviation


def merge_output_data(
    batch_output_dir: Path, output_dir: Path, batch_index: int
) -> int:
    f"""
    Copy a batch output data into a merged output directory.
    Some data is copied into their final destination, some in temporary location to be merged later by {reconstruct_synthesis.__name__}
    """
    mode = "economy"
    if not (batch_output_dir / mode).exists():
        mode = "adequacy"
    # mc-ind
    data_dir = batch_output_dir / mode / "mc-ind"
    if not data_dir.exists():
        logger.warning(f"Failed to find data dir in output {batch_output_dir}")
        return 0
    mc_years = os.listdir(data_dir)
    if output_dir == batch_output_dir:
        return len(mc_years)

    for mc_year in mc_years:
        shutil.move(
            str(data_dir / mc_year), output_dir / mode / "mc-ind" / mc_year
        )

    # temporary summary files and logs
    os.makedirs(output_dir / TMP_SUMMARIES_DIR, exist_ok=True)
    for src, target in [
        (
            batch_output_dir / "simulation.log",
            output_dir / f"simulation.log.{batch_index}",
        ),
        (
            batch_output_dir / mode / "mc-all",
            output_dir / TMP_SUMMARIES_DIR / f"mc-all.{batch_index}",
        ),
        (
            batch_output_dir / "checkIntegrity.txt",
            output_dir
            / TMP_SUMMARIES_DIR
            / f"checkIntegrity.txt.{batch_index}",
        ),
        (
            batch_output_dir / "annualSystemCost.txt",
            output_dir
            / TMP_SUMMARIES_DIR
            / f"annualSystemCost.txt.{batch_index}",
        ),
        (
            batch_output_dir / "about-the-study" / "parameters.ini",
            output_dir / TMP_SUMMARIES_DIR / f"parameters.ini.{batch_index}",
        ),
    ]:
        if src.exists():
            shutil.move(str(src), target)

    return len(mc_years)


def merge_summary_files(
    output_dir: Path,
    batches_indices_size: List[Tuple[int, int]],
) -> None:
    logger.info("Merging summary files")
    stats = []
    all_min = []
    all_max = []
    files_to_merge = [
        (
            output_dir / "checkIntegrity.txt",
            output_dir / "annualSystemCost.txt",
            batches_indices_size[0][1],
        )
    ]
    for batch_index, batch_size in batches_indices_size[1:]:
        files_to_merge.append(
            (
                output_dir
                / TMP_SUMMARIES_DIR
                / f"checkIntegrity.txt.{batch_index}",
                output_dir
                / TMP_SUMMARIES_DIR
                / f"annualSystemCost.txt.{batch_index}",
                batch_size,
            )
        )
    for file_to_merge in files_to_merge:
        exp_series = []
        std_series = []
        min_series = []
        max_series = []
        with open(file_to_merge[0]) as fh:
            data = fh.readlines()
            assert_this(len(data) >= 8)
            exp_series.append(float(data[0].strip()))
            exp_series.append(float(data[4].strip()))
            std_series.append(float(data[1].strip()))
            std_series.append(float(data[5].strip()))
            min_series.append(float(data[2].strip()))
            min_series.append(float(data[6].strip()))
            max_series.append(float(data[3].strip()))
            max_series.append(float(data[7].strip()))
        with open(file_to_merge[1]) as fh:
            data = fh.readlines()
            assert_this(len(data) >= 4)
            exp_series.append(float(data[0].split(":")[1].strip()))
            std_series.append(float(data[1].split(":")[1].strip()))
            min_series.append(float(data[2].split(":")[1].strip()))
            max_series.append(float(data[3].split(":")[1].strip()))
        stats.append(
            (Series(exp_series), Series(std_series), file_to_merge[2])
        )
        all_min.append(Series(min_series))
        all_max.append(Series(max_series))

    means, sqroots = merge_series_stats(stats)
    mins = DataFrame(all_min).min()
    maxs = DataFrame(all_max).max()
    with open(output_dir / "checkIntegrity.txt", "w") as fh:
        fh.write(f"{means[0]}\n")
        fh.write(f"{sqroots[0]}\n")
        fh.write(f"{mins[0]}\n")
        fh.write(f"{maxs[0]}\n")
        fh.write(f"{means[1]}\n")
        fh.write(f"{sqroots[1]}\n")
        fh.write(f"{mins[1]}\n")
        fh.write(f"{maxs[1]}\n")
    with open(output_dir / "annualSystemCost.txt", "w") as fh:
        fh.write(f"EXP : {means[2]}\n")
        fh.write(f"STD : {sqroots[2]}\n")
        fh.write(f"MIN : {mins[2]}\n")
        fh.write(f"MAX : {maxs[2]}\n")


def _reduce_types(
    agg: Dict[str, List[Tuple[str, str]]], el: Tuple[str, str, str]
) -> Dict[str, List[Tuple[str, str]]]:
    if el[2] == "EXP" or el[2] == "std":
        if el[:2] in agg["tmp_avg_and_std"]:
            agg["avg_and_std"].append(el[:2])
            agg["tmp_avg_and_std"].remove(el[:2])
        agg["tmp_avg_and_std"].append(el[:2])
    elif el[2] == "values":
        agg["vals"].append(el[:2])
    elif el[2] == "min":
        agg["min"].append(el[:2])
    elif el[2] == "max":
        agg["max"].append(el[:2])
    return agg


def _compare(compare_func: Callable[[float, float], bool]) -> Any:
    def do_compare(series: Series) -> Any:
        series_list = series.to_list()
        min_val = series_list[0]
        for el in series_list[1:]:
            if compare_func(el[0], min_val[0]):
                if el[0] == min_val[0]:
                    min_val = el if el[1] < min_val[1] else min_val
                else:
                    min_val = el
        return min_val

    return do_compare


def get_all_output_matrices(
    study: FileStudy,
    output_name: str,
    batches_indices_size: List[Tuple[int, int]],
) -> Any:
    """
    Args:
        study: a filestudy
        output_name: name of the output
        batches_indices_size: indices and weight size of the output parts to merge

    Returns:
        A tuple containing a dictionnary of all mc_data matrices structured by types and item, and the weight of the mc_data matrices
    """
    config = study.config.at_file(
        study.config.study_path
        / "output"
        / output_name
        / "economy"
        / f"mc-all"
    )

    mc_all = OutputSimulationModeMcAll(study.tree.context, config)
    mc_alls = [mc_all]
    mc_all_weights = [batches_indices_size[0][1]]
    for batch_index, batch_size in batches_indices_size[1:]:
        config = study.config.at_file(
            study.config.study_path
            / "output"
            / output_name
            / TMP_SUMMARIES_DIR
            / f"mc-all.{batch_index}"
        )
        mc_all = OutputSimulationModeMcAll(study.tree.context, config)
        mc_alls.append(mc_all)
        mc_all_weights.append(batch_size)

    # fetch all matrix data
    mc_data: Dict[str, Dict[str, Dict[str, List[OutputSeriesMatrix]]]] = {
        "areas": {},
        "links": {},
    }
    for batch_data in mc_alls:
        # fetch all area and set output series matrix nodes
        for key, child in (
            cast(FolderNode, batch_data.get_node(["areas"])).build().items()
        ):
            if key not in mc_data["areas"]:
                mc_data["areas"][key] = {}
            for data_key, data in cast(FolderNode, child).build().items():
                if data_key not in mc_data["areas"][key]:
                    mc_data["areas"][key][data_key] = []
                mc_data["areas"][key][data_key].append(
                    cast(OutputSeriesMatrix, data)
                )

        # fetch all links output series matrix nodes
        for child_key_0, child0 in (
            cast(FolderNode, batch_data.get_node(["links"])).build().items()
        ):
            for child_key_1, child1 in (
                cast(FolderNode, child0).build().items()
            ):
                child_key = f"{child_key_0} - {child_key_1}"
                if child_key not in mc_data["links"]:
                    mc_data["links"][child_key] = {}
                for data_key, data in cast(FolderNode, child1).build().items():
                    if data_key not in mc_data["links"][child_key]:
                        mc_data["links"][child_key][data_key] = []
                    mc_data["links"][child_key][data_key].append(
                        cast(OutputSeriesMatrix, data)
                    )
    return mc_data, mc_all_weights


def process_data(
    data_nodes: Dict[str, List[OutputSeriesMatrix]],
    stat_name: str,
    mc_all_weights: List[int],
) -> None:
    if "values" in stat_name or "details" in stat_name:
        dfs = [
            data_node.parse_dataframe() for data_node in data_nodes[stat_name]
        ]
        df_main = dfs[0]
        vals_types: Dict[str, List[Tuple[str, str]]] = reduce(
            _reduce_types,
            df_main.columns.values.tolist(),
            {
                "avg_and_std": [],
                "tmp_avg_and_std": [],
                "min": [],
                "max": [],
                "vals": [],
            },
        )

        dfs_id_main: Optional[DataFrame] = None
        dfs_id: List[DataFrame] = []
        df_id_datanode_name: Optional[str] = None
        if "values" in stat_name:
            freq_match = re.match("values-(\\w+)", stat_name)
            if freq_match:
                dfs_id = [
                    data_node.parse_dataframe()
                    for data_node in data_nodes[f"id-{freq_match.group(1)}"]
                ]
                dfs_id_main = dfs_id[0]
                df_id_datanode_name = f"id-{freq_match.group(1)}"

        for val_type in vals_types["avg_and_std"]:
            merged_data = merge_series_stats(
                [
                    (
                        cast(
                            Series,
                            df[(val_type[0], val_type[1], "EXP")],
                        ),
                        cast(
                            Series,
                            df[(val_type[0], val_type[1], "std")],
                        ),
                        mc_all_weights[i],
                    )
                    for i, df in enumerate(dfs)
                ]
            )
            df_main[(val_type[0], val_type[1], "EXP")] = merged_data[0]
            df_main[(val_type[0], val_type[1], "std")] = merged_data[1]
        for val_type in vals_types["min"]:
            col_key = (val_type[0], val_type[1], "min")
            if dfs_id_main is not None:
                df_tmp = DataFrame(
                    {i: df[col_key] for i, df in enumerate(dfs)}
                ).combine(
                    DataFrame({i: df[col_key] for i, df in enumerate(dfs_id)}),
                    lambda x, y: x.combine(y, lambda a, b: (a, b)),
                )
                df_res = df_tmp.apply(
                    _compare(operator.le), result_type="expand", axis=1
                )
                df_main[col_key] = df_res.iloc[:, 0]
                dfs_id_main[col_key] = df_res.iloc[:, 1]
            else:
                df_main[col_key] = DataFrame(
                    {i: df[col_key] for i, df in enumerate(dfs)}
                ).min(axis=1)
        for val_type in vals_types["max"]:
            col_key = (val_type[0], val_type[1], "max")
            if dfs_id_main is not None:
                df_tmp = DataFrame(
                    {i: df[col_key] for i, df in enumerate(dfs)}
                ).combine(
                    DataFrame({i: df[col_key] for i, df in enumerate(dfs_id)}),
                    lambda x, y: x.combine(y, lambda a, b: (a, b)),
                )
                df_res = df_tmp.apply(
                    _compare(operator.ge), result_type="expand", axis=1
                )
                df_main[col_key] = df_res.iloc[:, 0]
                dfs_id_main[col_key] = df_res.iloc[:, 1]
            else:
                df_main[col_key] = DataFrame(
                    {i: df[col_key] for i, df in enumerate(dfs)}
                ).max(axis=1)
        for val_type_name in ["tmp_avg_and_std", "vals"]:
            col_type_name = (
                "EXP" if val_type_name == "tmp_avg_and_std" else "values"
            )
            for val_type in vals_types[val_type_name]:
                col_key = (val_type[0], val_type[1], col_type_name)
                logger.info(col_key)
                df_main[col_key] = (
                    DataFrame(
                        {
                            i: df[col_key].mul(mc_all_weights[i])
                            for i, df in enumerate(dfs)
                        }
                    )
                    .sum(axis=1, skipna=False)
                    .div(np.sum(mc_all_weights))
                )

        data_nodes[stat_name][0].save(df_main.to_dict(orient="split"))
        if dfs_id_main is not None and df_id_datanode_name:
            data_nodes[df_id_datanode_name][0].save(
                dfs_id_main.astype("int64", errors="ignore").to_dict(
                    orient="split"
                )
            )


def reconstruct_synthesis(
    study: FileStudy,
    output_name: str,
    batches_indices_size: List[Tuple[int, int]],
) -> None:
    """
    Merge all synthesis data:
    - mc-all
    - todo parameters (playlist)
    - summary files (checkIntegrity.txt, annualSystemCost.txt)
    - todo ts numbers
    """
    # merge "summary files"
    merge_summary_files(
        study.config.study_path / "output" / output_name,
        batches_indices_size,
    )

    # list every batch mc all folder nodes
    mc_data, mc_all_weights = get_all_output_matrices(
        study, output_name, batches_indices_size
    )

    for item_type in ["areas", "links"]:
        for item in mc_data[item_type]:
            for stat_element in mc_data[item_type][item]:
                logger.info(
                    f"Processing {stat_element} for {item_type} {item}"
                )
                process_data(
                    mc_data[item_type][item], stat_element, mc_all_weights
                )
