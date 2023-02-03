from typing import Optional, List, cast, Dict

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    get_playlist,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: Optional[str] = None) -> JSON:
        if output_id:
            config_path = [
                "output",
                output_id,
                "about-the-study",
                "parameters",
            ]
            config = study.tree.get(config_path)
            return config
        return study.tree.get(["settings", "generaldata"])

    @staticmethod
    def save_config(study: FileStudy, config: JSON) -> None:
        config_path = ["settings", "generaldata"]
        return study.tree.save(config, config_path)

    @staticmethod
    def get_playlist(
        study: FileStudy, output_id: Optional[str] = None
    ) -> Optional[Dict[int, float]]:
        config = FileStudyHelpers.get_config(study, output_id)
        return get_playlist(config)

    @staticmethod
    def set_playlist(
        study: FileStudy,
        playlist: List[int],
        weights: Optional[Dict[int, float]] = None,
        reverse: bool = False,
        active: bool = True,
    ) -> None:
        playlist_without_offset = [year - 1 for year in playlist]
        config = FileStudyHelpers.get_config(study)
        general_config: Optional[JSON] = config.get("general", None)
        assert_this(general_config is not None)
        general_config = cast(JSON, general_config)
        nb_years = cast(int, general_config.get("nbyears"))
        playlist_config = config.get("playlist", {})
        if reverse:
            playlist_without_offset = [
                year
                for year in range(0, nb_years)
                if year not in playlist_without_offset
            ]
        general_config["user-playlist"] = active
        if len(playlist_without_offset) > nb_years / 2:
            playlist_config["playlist_reset"] = True
            if "playlist_year +" in playlist_config:
                del playlist_config["playlist_year +"]
            playlist_config["playlist_year -"] = [
                year
                for year in range(0, nb_years)
                if year not in playlist_without_offset
            ]
        else:
            playlist_config["playlist_reset"] = False
            if "playlist_year -" in playlist_config:
                del playlist_config["playlist_year -"]
            playlist_config["playlist_year +"] = playlist_without_offset

        if "playlist_year_weight" in playlist_config:
            del playlist_config["playlist_year_weight"]
        if weights:
            playlist_config["playlist_year_weight"] = [
                f"{year - 1},{weight}" for year, weight in weights.items()
            ]
        config["playlist"] = playlist_config
        FileStudyHelpers.save_config(study, config)
