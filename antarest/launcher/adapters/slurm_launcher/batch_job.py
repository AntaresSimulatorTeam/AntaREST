import logging
import math
import os
import re
import shutil
import uuid
from functools import reduce
from pathlib import Path
from typing import Dict, Optional, List, Tuple, cast, Any

from filelock import FileLock
from pandas import Series, MultiIndex, DataFrame

from antareslauncher.study_dto import StudyDTO
from antarest.core.config import Config
from antarest.core.configdata.model import ConfigData
from antarest.core.configdata.repository import ConfigDataRepository
from antarest.core.utils.fastapi_sqlalchemy import db
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import (
    FileStudy,
    StudyFactory,
)
from antarest.study.storage.rawstudy.model.filesystem.folder_node import (
    FolderNode,
)
from antarest.study.storage.rawstudy.model.filesystem.matrix.output_series_matrix import (
    AreaOutputSeriesMatrix,
    OutputSeriesMatrix,
)
from antarest.study.storage.rawstudy.model.filesystem.root.output.simulation.mode.mcall.mcall import (
    OutputSimulationModeMcAll,
)
from antarest.study.storage.rawstudy.model.helpers import FileStudyHelpers
from antarest.study.storage.utils import find_single_output_path


logger = logging.getLogger(__name__)

BATCH_JOB_CONFIG_DATA_KEY = "BATCH_JOBS"
TMP_SUMMARIES_DIR = "tmp_summaries"


class BatchJobManager:
    def __init__(
        self, workspace_id: str, study_factory: StudyFactory, config: Config
    ):
        self.batch_size = config.launcher.batch_size
        self.config_data_repo = ConfigDataRepository()
        self.study_factory = study_factory
        self.lock_file = config.storage.tmp_dir / "batchjobmanager.lock"
        self.workspace_id = workspace_id
        self.cache: Dict[str, str] = {}

    def refresh_cache(self) -> None:
        self.cache = self._get_batch_jobs()

    def _get_batch_jobs(self) -> Dict[str, str]:
        with db():
            all_jobs = (
                self.config_data_repo.get_json(key=BATCH_JOB_CONFIG_DATA_KEY)
                or {}
            )
            return all_jobs.get(self.workspace_id, {})

    def _add_batch_job(
        self, parent_job_id: str, batch_job_ids: List[str]
    ) -> None:
        with FileLock(self.lock_file):
            with db():
                all_jobs = (
                    self.config_data_repo.get_json(
                        key=BATCH_JOB_CONFIG_DATA_KEY
                    )
                    or {}
                )
                workspace_jobs = all_jobs.get(self.workspace_id, {})
                for batch_job_id in batch_job_ids:
                    workspace_jobs[batch_job_id] = parent_job_id
                all_jobs[self.workspace_id] = workspace_jobs
                self.config_data_repo.put_json(
                    key=BATCH_JOB_CONFIG_DATA_KEY, data=all_jobs
                )
                self.cache = workspace_jobs

    def remove_batch_job(self, parent_job_id: str) -> None:
        with FileLock(self.lock_file):
            with db():
                all_jobs = (
                    self.config_data_repo.get_json(
                        key=BATCH_JOB_CONFIG_DATA_KEY
                    )
                    or {}
                )
                workspace_jobs = all_jobs.get(self.workspace_id, {})
                workspace_jobs = {
                    job_id: parent_id
                    for job_id, parent_id in workspace_jobs.items()
                    if parent_id != parent_job_id
                }
                all_jobs[self.workspace_id] = workspace_jobs
                self.config_data_repo.put_json(
                    key=BATCH_JOB_CONFIG_DATA_KEY, data=all_jobs
                )
                self.cache = workspace_jobs

    def get_batch_job_parent(self, batch_job_id: str) -> Optional[str]:
        return self.cache.get(batch_job_id, None)

    def get_batch_job_children(self, parent_batch_job_id: str) -> List[str]:
        return [
            child
            for child, parent in self.cache.items()
            if parent_batch_job_id == parent
        ]

    @staticmethod
    def compute_batch_params(
        study: FileStudy, batch_size: int
    ) -> List[List[int]]:
        """
        Compute list of playlist years which count do not exceed a configured batch size.
        """
        playlist = FileStudyHelpers.get_playlist(study)
        playlist_len = len(playlist)
        if playlist_len > batch_size:
            batchs = []
            i = 0
            while True:
                upper_bound = batch_size * (1 + i)
                if upper_bound >= playlist_len:
                    batchs.append(playlist[batch_size * i : playlist_len])
                    break
                batchs.append(playlist[batch_size * i : upper_bound])
                i += 1
            return batchs
        return [playlist]

    def prepare_batch_study(
        self,
        job_id: str,
        raw_study_path: Path,
        workspace: Path,
        force_single_batch: bool = False,
    ) -> List[str]:
        """
        Split a study into multiple batches using playlist to control which year to run.
        The study is copied into a new directory named after the sub job id and generaldata playlist is updated.
        The the array of sub job is registered with reference to the original job_id as parent.

        If the configured playlist / number of year to run is less than a batch configured size or forced to use a single batch
        nothing is done and the sub job id is the same as the parent id
        """
        study = self.study_factory.create_from_fs(
            raw_study_path, study_id=job_id
        )
        batch_params = (
            BatchJobManager.compute_batch_params(study, self.batch_size)
            if not force_single_batch
            else []
        )

        if len(batch_params) <= 1:
            self._add_batch_job(job_id, [job_id])
            return [job_id]

        FileStudyHelpers.set_playlist(study, batch_params[0])
        sub_jobs = []
        for playlist in batch_params[1:]:
            sub_job_id = str(uuid.uuid4())
            shutil.copytree(raw_study_path, workspace / sub_job_id)
            study = self.study_factory.create_from_fs(
                workspace / sub_job_id, study_id=job_id
            )
            FileStudyHelpers.set_playlist(study, playlist)
            sub_jobs.append(sub_job_id)

        sub_job_id = str(uuid.uuid4())
        shutil.move(str(raw_study_path), str(workspace / sub_job_id))
        sub_jobs.append(sub_job_id)
        self._add_batch_job(job_id, sub_jobs)
        return sub_jobs

    def merge_outputs(
        self,
        job_id: str,
        launcher_studies: List[StudyDTO],
        workspace: Path,
        allow_part_failure: bool = True,
    ) -> Optional[Path]:
        """
        Merge the output of study run batches.
        The first output directory found (study done with no error) is taken as the main output where everything will be merged.
        This way, in the case of a single batch, nothing is done.
        Merging is done in two steps:
        - copying each output data in the correct place (mc-ind) or temporary places (mc-all, synthesis files, parameters)
        - merging the synthesis
        """
        assert_this(len(launcher_studies) > 0)
        output_dir: Optional[Path] = None
        output_info: Optional[Tuple[Path, str]] = None
        batch_parts = 0
        merged_batches = {}
        for study in launcher_studies:
            if not study.with_error:
                batch_parts += 1
                batch_output_dir = find_single_output_path(
                    workspace / study.name / "output"
                )
                if not output_dir:
                    output_dir = batch_output_dir
                    output_info = (
                        workspace / study.name,
                        batch_output_dir.name,
                    )
                else:
                    batch_size = self.merge_output_data(
                        batch_output_dir, output_dir, batch_parts
                    )
                    merged_batches[batch_parts] = batch_size
            elif not allow_part_failure:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Importing nothing."
                )
                return None
            else:
                logger.warning(
                    f"Sub job {study.name} failed within job {job_id}. Skipping importing this part."
                )
        if batch_parts > 1 and output_info:
            self.reconstruct_synthesis(
                output_info[0], output_info[1], merged_batches
            )
        return output_dir

    @staticmethod
    def merge_series_stats(
        stats: List[Tuple[Series, Series, int]]
    ) -> Tuple[Series, Series]:
        def compute_stats(
            agg: Optional[Tuple[Series, Series, int]],
            el: Tuple[Series, Series, int],
        ) -> Tuple[Series, Series, int]:
            avg, sqr_root_std_dev, n = el
            if agg:
                agg_x, agg_mean, agg_total = agg
                return (
                    agg_x.add(
                        (sqr_root_std_dev.pow(2) + avg.pow(2)).multiply(n)
                    ),
                    agg_mean.add(avg.multiply(n)),
                    agg_total + n,
                )
            else:
                return (
                    (sqr_root_std_dev.pow(2) + avg.pow(2)).multiply(n),
                    avg.multiply(n),
                    n,
                )

        e_x2, e_total, n = reduce(compute_stats, stats, None)
        sqrt_root_std_deviation = (
            e_x2.divide(n).sub(e_total.divide(n).pow(2)).pow(0.5)
        )
        mean = e_total / n
        return mean, sqrt_root_std_deviation

    @staticmethod
    def merge_stats(
        stats: List[Tuple[float, float, int]]
    ) -> Tuple[float, float]:
        """
        Merge statistical data (mean and square root variance)
        Args:
            stats: list of statistical data containing tuples of mean, square root variance and dataset count
        Returns:
            a tuple containing the merged mean and square root variance
        """

        def compute_stats(
            agg: Tuple[float, float, int], el: Tuple[float, float, int]
        ) -> Tuple[float, float, int]:
            agg_x, agg_mean, agg_total = agg
            avg, sqr_root_std_dev, n = el
            return (
                agg_x + n * (math.pow(sqr_root_std_dev, 2) + math.pow(avg, 2)),
                agg_mean + avg * n,
                agg_total + n,
            )

        e_x2, e_total, n = reduce(compute_stats, stats, (0.0, 0.0, 0))
        sqrt_root_std_deviation = math.sqrt(
            (e_x2 / n) - math.pow(e_total / n, 2)
        )
        mean = e_total / n
        return mean, sqrt_root_std_deviation

    @staticmethod
    def merge_output_data(
        batch_output_dir: Path, output_dir: Path, batch_index: int
    ) -> int:
        f"""
        Copy a batch output data into a merged output directory.
        Some data is copied into their final destination, some in temporary location to be merged later by {BatchJobManager.reconstruct_synthesis.__name__}
        """
        mode = "economy"
        if not (batch_output_dir / mode).exists():
            mode = "adequacy"
        # mc-ind
        data_dir = batch_output_dir / mode / "mc-ind"
        if not data_dir.exists():
            logger.warning(
                f"Failed to find data dir in output {batch_output_dir}"
            )
            return 0
        mc_years = os.listdir(data_dir)
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
                output_dir
                / TMP_SUMMARIES_DIR
                / f"parameters.ini.{batch_index}",
            ),
        ]:
            if src.exists():
                shutil.move(str(src), target)

        return len(mc_years)

    def reconstruct_synthesis(
        self,
        study_dir: Path,
        output_name: str,
        batches_indices_size: Dict[int, int],
    ) -> None:
        """
        Merge all synthesis data:
        - mc-all
        - todo parameters (playlist)
        - todo summary files (checkIntegrity.txt, annualSystemCost.txt)
        """
        study = self.study_factory.create_from_fs(
            study_dir, "", use_cache=False
        )

        config = study.config.at_file(
            study.config.study_path
            / "output"
            / output_name
            / "economy"
            / f"mc-all"
        )
        mc_all = OutputSimulationModeMcAll(study.tree.context, config)
        mc_alls = [mc_all]
        mc_alls_size = [self.batch_size]
        for batch_index in batches_indices_size:
            config = study.config.at_file(
                study.config.study_path
                / "output"
                / output_name
                / TMP_SUMMARIES_DIR
                / f"mc-all-{batch_index}"
            )
            mc_all = OutputSimulationModeMcAll(study.tree.context, config)
            mc_alls.append(mc_all)
            mc_alls_size.append(batches_indices_size[batch_index])

        mc_data: Dict[str, Dict[str, Dict[str, List[OutputSeriesMatrix]]]] = {
            "areas": {},
            "links": {},
        }
        for batch_data in mc_alls:
            for key, child in (
                cast(FolderNode, batch_data.get_node(["areas"]))
                .build()
                .items()
            ):
                if key not in mc_data["areas"]:
                    mc_data["areas"][key] = {}
                for data_key, data in cast(FolderNode, child).build().items():
                    if data_key not in mc_data["areas"][key]:
                        mc_data["areas"][key][data_key] = []
                    mc_data["areas"][key][data_key].append(
                        cast(OutputSeriesMatrix, data)
                    )
            for child_key_0, child0 in (
                cast(FolderNode, batch_data.get_node(["links"]))
                .build()
                .items()
            ):
                for child_key_1, child1 in (
                    cast(FolderNode, child0).build().items()
                ):
                    child_key = f"{child_key_0} - {child_key_1}"
                    if child_key not in mc_data["links"]:
                        mc_data["links"][child_key] = {}
                    for data_key, data in (
                        cast(FolderNode, child1).build().items()
                    ):
                        if data_key not in mc_data["links"][child_key]:
                            mc_data["links"][child_key][data_key] = []
                        mc_data["links"][child_key][data_key].append(
                            cast(OutputSeriesMatrix, data)
                        )

        def reduce_types(
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

        def process_data(
            data_nodes: Dict[str, List[OutputSeriesMatrix]], stat_name: str
        ) -> None:
            if "values" in stat_name or "details" in stat_name:
                dfs = [
                    data_node.parse_dataframe()
                    for data_node in data_nodes[stat_name]
                ]
                dfs_id: List[DataFrame] = []
                if "values" in stat_name:
                    freq_match = re.match("values-(\\w+)", stat_name)
                    dfs_id = [
                        data_node.parse_dataframe()
                        for data_node in data_nodes[
                            f"values-{freq_match.group(1)}"
                        ]
                    ]
                df_main = dfs[0]
                vals_types = reduce(
                    reduce_types,
                    df_main.columns.values.tolist(),
                    {
                        "avg_and_std": [],
                        "tmp_avg_and_std": [],
                        "min": [],
                        "max": [],
                        "vals": [],
                    },
                )
                for val_type in vals_types["avg_and_std"]:
                    merged_data = BatchJobManager.merge_series_stats(
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
                                mc_alls_size[i],
                            )
                            for i, df in enumerate(dfs)
                        ]
                    )
                    df_main[(val_type[0], val_type[1], "EXP")] = merged_data[0]
                    df_main[(val_type[0], val_type[1], "std")] = merged_data[1]
                for val_type in vals_types["min"]:
                    for df in dfs[1:]:
                        col_key = (val_type[0], val_type[1], "min")
                        df_main[col_key] = DataFrame(
                            {"1": df_main[col_key], "2": df[col_key]}
                        ).min(axis=1)
                    # todo fetch the correct df id from dfs_id
                for val_type in vals_types["max"]:
                    for df in dfs[1:]:
                        col_key = (val_type[0], val_type[1], "min")
                        df_main[col_key] = DataFrame(
                            {"1": df_main[col_key], "2": df[col_key]}
                        ).max(axis=1)
                    # todo fetch the correct df id from dfs_id
                for val_type_name in ["tmp_avg_and_std", "vals"]:
                    col_type_name = (
                        "EXP"
                        if val_type_name == "tmp_avg_and_std"
                        else "values"
                    )
                    for val_type in vals_types[val_type_name]:
                        col_key = (val_type[0], val_type[1], col_type_name)
                        logger.info(col_key)
                        df_main[col_key] = DataFrame(
                            {i: df[col_key] for i, df in enumerate(dfs)}
                        ).mean(axis=1)

                data_nodes[stat_name][0].save(df_main.to_dict(orient="split"))

        for item_type in ["areas", "links"]:
            for item in mc_data[item_type]:
                for stat_element in mc_data[item_type][item]:
                    logger.info(
                        f"Processing {stat_element} for {item_type} {item}"
                    )
                    process_data(mc_data[item_type][item], stat_element)
