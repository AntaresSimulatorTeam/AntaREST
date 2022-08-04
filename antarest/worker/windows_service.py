import sys
from pathlib import Path

from antarest.core.config import Config
from antarest.core.logging.utils import configure_logger
from antarest.core.utils.utils import get_local_path
from antarest.main import init_db, create_archive_worker


if __name__ == '__main__':
    res = get_local_path() / "resources"
    if len(sys.argv) <= 1:
        sys.exit(1)
    config_file = Path(sys.argv[1])
    config = Config.from_yaml_file(res=res, file=config_file)
    configure_logger(config)
    init_db(config_file, config, False, None)
    worker = create_archive_worker(config, "aws_share_2")
    worker.start()

