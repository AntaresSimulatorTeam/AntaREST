"""
Antares Simulator Artifact Downloader
"""
import dataclasses
import datetime
import json
import pathlib
import re
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional

from antarest.packaging.platform_detector import Platform


@dataclasses.dataclass
class Asset:
    name: str
    url: str

    @classmethod
    def from_obj(cls, obj: Dict[str, str]) -> "Asset":
        return cls(name=obj["name"], url=obj["browser_download_url"])

    def download(
        self,
        dst_dir: pathlib.Path,
    ) -> pathlib.Path:
        with urllib.request.urlopen(self.url) as response:
            data = response.read()
        asset_path = dst_dir.joinpath(self.name)
        with asset_path.open(mode="wb") as f:
            f.write(data)
        return asset_path


@dataclasses.dataclass(order=True)
class Release:
    tag_name: str = dataclasses.field(compare=False)
    published_at: datetime.datetime = dataclasses.field(compare=True)
    draft: bool = dataclasses.field(compare=False)
    # noinspection SpellCheckingInspection
    prerelease: bool = dataclasses.field(compare=False)
    body: str = dataclasses.field(compare=False)
    assets: List[Asset] = dataclasses.field(compare=False)

    @classmethod
    def from_obj(cls, obj: Dict[str, Any]) -> "Release":
        published_at = datetime.datetime.fromisoformat(
            obj["published_at"].rstrip("Z")
        )
        return cls(
            tag_name=obj["tag_name"],
            published_at=published_at,
            draft=bool(obj["draft"]),
            prerelease=bool(obj["prerelease"]),
            body=obj["body"],
            assets=[Asset.from_obj(o) for o in obj["assets"]],
        )

    def find_asset(self, local_platform: Optional[Platform] = None) -> Asset:
        if local_platform is None:
            local_platform = Platform.auto_detect()
        asset_patterns = {
            Platform.WINDOWS: "rte-antares-.*-installer-64bits.zip",
            Platform.UBUNTU: "antares-.*-Ubuntu-20.04.tar.gz",
            Platform.CENT_OS: "antares-.*-CentOS-7.9.2009.tar.gz",
        }
        pattern = asset_patterns[local_platform]
        for asset in self.assets:
            if re.fullmatch(pattern, asset.name):
                return asset
        raise RuntimeError(f"Failed to retrieve asset matching '{pattern}'")


class AntaresSimulatorDownloader:
    repo = "AntaresSimulatorTeam/Antares_Simulator"
    url = f"https://api.github.com/repos/{repo}/releases"

    def __init__(self) -> None:
        with urllib.request.urlopen(self.url) as response:
            data = response.read()
        if data:
            obj = json.loads(data.decode())
            self.releases = [Release.from_obj(o) for o in obj]
        else:
            raise RuntimeError(f"Failed to retrieve data from {self.url}")

    @property
    def latest_release(self) -> Release:
        # noinspection PyTypeChecker
        releases = sorted(
            (r for r in self.releases if not r.draft and not r.prerelease),
            reverse=True,
        )
        return releases[0]

    def download_asset(
        self,
        dst_dir: pathlib.Path,
        local_platform: Optional[Platform] = None,
    ) -> pathlib.Path:
        asset = self.latest_release.find_asset(local_platform=local_platform)
        return asset.download(dst_dir)
