import tempfile
from typing import Optional, List, cast
from zipfile import ZipFile, Path

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.io.reader import MultipleSameKeysIniReader
from antarest.study.storage.rawstudy.model.filesystem.config.files import (
    ConfigPathBuilder,
)
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy
from antarest.study.storage.rawstudy.model.filesystem.root.settings.generaldata import (
    DUPLICATE_KEYS,
)


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: Optional[str] = None) -> JSON:
        config_path = ["settings", "generaldata"]
        if output_id:
            if study.config.outputs[output_id].archived:
                # TODO: remove this part of code when study tree zipfile support is implemented
                output_path = study.config.output_path / f"{output_id}.zip"
                tmp_dir = tempfile.TemporaryDirectory()
                with ZipFile(output_path, "r") as zip_obj:
                    zip_obj.extract(
                        str(
                            output_path / "about-the-study" / "parameters.ini"
                        ),
                        tmp_dir.name,
                    )
                    full_path_parameters = (
                        Path(tmp_dir.name)
                        / "about-the-study"
                        / "parameters.ini"
                    )
                config = MultipleSameKeysIniReader(DUPLICATE_KEYS).read(
                    full_path_parameters
                )
                tmp_dir.cleanup()
            else:
                config_path = [
                    "output",
                    output_id,
                    "about-the-study",
                    "parameters",
                ]
                config = study.tree.get(config_path)
            return config
        return study.tree.get(config_path)

    @staticmethod
    def save_config(study: FileStudy, config: JSON) -> None:
        config_path = ["settings", "generaldata"]
        return study.tree.save(config, config_path)

    @staticmethod
    def get_playlist(
        study: FileStudy, output_id: Optional[str] = None
    ) -> Optional[List[int]]:
        config = FileStudyHelpers.get_config(study, output_id)
        return ConfigPathBuilder.get_playlist(config)

    @staticmethod
    def set_playlist(study: FileStudy, playlist: List[int]) -> None:
        playlist_without_offset = [year - 1 for year in playlist]
        config = FileStudyHelpers.get_config(study)
        general_config: Optional[JSON] = config.get("general", None)
        assert_this(general_config is not None)
        general_config = cast(JSON, general_config)
        nb_years = cast(int, general_config.get("nbyears"))
        if len(playlist) == nb_years:
            general_config["user-playlist"] = False
        else:
            playlist_config = config.get("playlist", {})
            general_config["user-playlist"] = True
            if len(playlist) > nb_years / 2:
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
            config["playlist"] = playlist_config
        FileStudyHelpers.save_config(study, config)
