"""
Entry point of this package
"""
import argparse
import logging
import pathlib
import re
import shutil
import signal
import sys
import tempfile
import textwrap
from typing import Optional, Sequence

from antarest import __date__ as release_date
from antarest import __version__ as app_version
from antarest.packaging.downloader import AntaresSimulatorDownloader
from antarest.packaging.exceptions import PackagingException
from antarest.packaging.platform_detector import Platform

# fmt: off
HERE = pathlib.Path(__file__).parent.resolve()
PROJECT_DIR = next(iter(p for p in HERE.parents if p.joinpath("antarest").is_dir()))
DIST_DIR = PROJECT_DIR.joinpath("dist")
RESOURCES_DIR = PROJECT_DIR.joinpath("resources")
# fmt: on

logger = logging.getLogger("antarest.packaging")


def dir_type(string: str) -> pathlib.Path:
    path = pathlib.Path(string).expanduser()
    if path.is_dir():
        return path
    raise argparse.ArgumentTypeError(f"Directory '{path}' not found")


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    prog = "package_antares_web"
    description = textwrap.dedent(
        f"""\
        Prepare the AntaresWebServer application for binary distribution
        
        Usage example:
        
          {prog} {DIST_DIR}
        """
    )
    parser = argparse.ArgumentParser(
        prog,
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{app_version} ({release_date})",
    )
    parser.add_argument(
        "--platform",
        choices=[p.value for p in Platform],
        help="Name of the local platform (auto-detected if missing)",
    )
    parser.add_argument(
        "dist_dir",
        metavar="DIST_DIR",
        type=dir_type,
        help=f"Target directory used to store the package to distribute (eg.: '{DIST_DIR}')",
    )
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None):
    namespace = parse_args(args)
    try:
        package_antares_web(namespace.dist_dir, namespace.platform)
    except PackagingException as exc:
        logger.error(str(exc))
        raise SystemExit(signal.SIGTERM) from None
    except KeyboardInterrupt:
        logger.error("Packaging cancelled by user")
        raise SystemExit(signal.SIGINT) from None
    except Exception as exc:
        logger.critical("Unhandled exception during packaging", exc_info=True)
        raise SystemExit(signal.SIGABRT) from exc


def package_antares_web(
    dist_dir: pathlib.Path,
    local_platform: Optional[Platform],
) -> None:
    local_platform = Platform(local_platform) if local_platform else Platform.auto_detect()
    
    solver_dir = dist_dir.joinpath("AntaresWeb/antares_solver")

    # logger.info(f"Preparing package for {local_platform.value}...")
    downloader = AntaresSimulatorDownloader()
    # with tempfile.TemporaryDirectory(
    #     dir=dist_dir,
    #     prefix="~download-",
    #     suffix=".tmp",
    # ) as dst_dir:
    #     # sourcery skip: extract-method
    #     logger.info(
    #         f"Downloading Antares Simulator {downloader.latest_release.tag_name}"
    #         f" archive in directory '{dst_dir}'..."
    #     )
    #     asset_path = downloader.download_asset(pathlib.Path(dst_dir), local_platform)
    #     logger.info(f"Uncompress the archive '{asset_path}' in directory '{solver_dir}'...")
    #     shutil.rmtree(solver_dir, ignore_errors=True)
    #     solver_dir.mkdir(parents=True)
    #     shutil.unpack_archive(asset_path, solver_dir)

    # logger.info(f"Move executable files in directory '{solver_dir}'...")
    # if local_platform == Platform.WINDOWS:
    #     patterns = ["*/bin/antares-*-solver.exe", "*/bin/sirius_solver.dll", "*/bin/zlib1.dll"]
    # else:
    #     # noinspection SpellCheckingInspection
    #     patterns = ["*/bin/antares-*-solver", "*/bin/libsirius_solver.so"]
    # for pattern in patterns:
    #     for path in solver_dir.glob(pattern):
    #         path.rename(solver_dir.joinpath(path.name))

    logger.info(f"Copying the deployment resources in '{dist_dir}'...")
    shutil.copytree(RESOURCES_DIR.joinpath("deploy"), dist_dir, dirs_exist_ok=True)

    config_yaml = dist_dir.joinpath("config.yaml")
    solver_version = downloader.latest_release.tag_name.replace("v", "").replace(".", "")
    solver_path = next(iter(solver_dir.glob("antares-*-solver*")))
    solver_relpath = solver_path.relative_to(dist_dir).as_posix()

    logger.info(f"Patching the configuration file {config_yaml}...")
    with config_yaml.open(mode="r+", encoding="utf-8") as fd:
        content = fd.read()
        content = re.sub(r"700: path/to/700", f"{solver_version}: ./{solver_relpath}", content, flags=re.DOTALL)
        fd.seek(0)
        fd.write(content)

    logger.info("Creating shortcuts...")
    if local_platform == Platform.WINDOWS:
        pass
    else:
        pass


if __name__ == "__main__":
    # noinspection SpellCheckingInspection
    logging.basicConfig(
        format="%(levelname)7s: %(name)s: %(message)s",
        level=logging.DEBUG,
    )
    main(sys.argv[1:])
