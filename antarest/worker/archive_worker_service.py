import argparse
import sys
from pathlib import Path

from antarest.core.config import Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.main import create_archive_worker
from antarest import __version__


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="path to the config file",
    )
    parser.add_argument(
        "-v",
        "--version",
        dest="version",
        help="Worker version",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-w",
        "--workspace",
        dest="workspace",
        help="Define the workspace associated with this worker",
        required=True,
    )
    parser.add_argument(
        "-l",
        "--local_root",
        dest="local_root",
        help="Define the local root path",
        required=False,
    )
    return parser.parse_args()


if __name__ == "__main__":
    res = get_local_path() / "resources"
    args = parse_arguments()
    if args.version:
        print(__version__)
        sys.exit()
    config_file = Path(args.config_file)
    local_root = Path(args.local_root or "/")
    workspace = args.workspace
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)
    worker = create_archive_worker(config, workspace, Path(local_root))
    worker.start()
