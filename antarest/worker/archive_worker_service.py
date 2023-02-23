import argparse
from pathlib import Path
from typing import Sequence, Optional

from antarest.core.config import Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest import __version__
from antarest.utils import create_archive_worker

ArgsType = Optional[Sequence[str]]


def parse_arguments(args: ArgsType = None) -> argparse.Namespace:
    version = f'%(prog)s {__version__}'
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        help="Display worker version and exit",
        action="version",
        version=version,
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="path to the config file",
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
        "--local-root",
        "--local_root",
        dest="local_root",
        help="Define the local root path",
        required=False,
    )
    return parser.parse_args(args)


def run_archive_worker(args: ArgsType = None) -> None:
    res = get_local_path() / "resources"
    namespace = parse_arguments(args)
    config_file = Path(namespace.config_file)
    local_root = Path(namespace.local_root or "/")
    workspace = namespace.workspace
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)
    worker = create_archive_worker(config, workspace, Path(local_root))
    worker.start(threaded=False)


if __name__ == "__main__":
    run_archive_worker()
