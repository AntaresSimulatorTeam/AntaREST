import typing
import zipfile
from pathlib import Path

import pytest


class AssetNotFoundError(FileNotFoundError):
    def __init__(self, asset_dir: Path, reason: str):
        msg = (
            f"Asset not found in '{asset_dir}': {reason}."
            f"\nMake sure that the resource files are available in the unit tests"
            f" and that you have named them correctly according to the module"
            f" name and the test function name (without the `test_` prefix)."
        )
        super().__init__(msg)


class StudyAssets(typing.NamedTuple):
    study_dir: Path
    expected_dir: Path


@pytest.fixture(name="study_assets", scope="function")
def study_assets(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> StudyAssets:
    """
    Fixture that provides study assets for a test function.
    Extract `{study}.zip` and `{study}.expected.zip` assets in the temporary path.

    Args:
        request: Fixture request object for the test function.
        tmp_path: Path to a temporary directory for the test session.

    Returns:
        StudyAssets: An object that contains the paths to directories
        for the study and expected study assets.

    Raises:
        AssetNotFoundError: If the study or expected study assets are not found
        in the resource directory.
    """
    module_path = Path(request.fspath)
    assets_dir = module_path.parent.joinpath(
        module_path.stem.replace("test_", "")
    )
    asset_dir = assets_dir.joinpath(request.node.name.replace("test_", ""))
    zip_files = list(asset_dir.glob("*.zip"))
    # find the study ZIP and uncompress it
    try:
        zip_path = next(iter(p for p in zip_files if p.suffixes == [".zip"]))
    except StopIteration:
        raise AssetNotFoundError(asset_dir, "no '{study}.zip' file") from None
    study_dir = tmp_path.joinpath(zip_path.stem)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(study_dir)
    # find the expected study ZIP and uncompress it
    try:
        zip_path = next(
            iter(p for p in zip_files if p.suffixes == [".expected", ".zip"])
        )
    except StopIteration:
        raise AssetNotFoundError(
            asset_dir, "no '{study}.expected.zip' file"
        ) from None
    expected_dir = tmp_path.joinpath(zip_path.stem)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(expected_dir)
    return StudyAssets(study_dir, expected_dir)
