from typing import Optional, List, cast

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: Optional[str] = None) -> JSON:
        config_path = ["settings", "generaldata"]
        if output_id:
            config_path = [
                "output",
                output_id,
                "about-the-study",
                "parameters",
            ]
        return study.tree.get(config_path)

    @staticmethod
    def save_config(study: FileStudy, config: JSON) -> None:
        config_path = ["settings", "generaldata"]
        return study.tree.save(config, config_path)

    @staticmethod
    def get_playlist(study: FileStudy) -> List[int]:
        config = FileStudyHelpers.get_config(study)
        nb_years = cast(int, config.get("general", {}).get("nbyears"))
        playlist_reset = config.get("playlist_reset", True)
        added = config.get("playlist_year +", [])
        removed = config.get("playlist_year -", [])
        if playlist_reset:
            return [year for year in range(0, nb_years) if year not in removed]
        return [year for year in added if year not in removed]

    @staticmethod
    def set_playlist(study: FileStudy, playlist: List[int]) -> None:
        config = FileStudyHelpers.get_config(study)
        general_config: Optional[JSON] = config.get("general", None)
        assert_this(general_config is not None)
        general_config = cast(JSON, general_config)
        nb_years = cast(int, general_config.get("nbyears"))
        if len(playlist) > nb_years / 2:
            general_config["playlist_reset"] = True
            general_config["playlist_year -"] = [
                year for year in range(0, nb_years) if year not in playlist
            ]
        else:
            general_config["playlist_reset"] = False
            general_config["playlist_year +"] = playlist
        FileStudyHelpers.save_config(study, config)
