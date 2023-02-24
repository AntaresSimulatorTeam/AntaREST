from unittest.mock import Mock, patch

import pytest
import yaml

from antarest import __version__
from antarest.worker.archive_worker import ArchiveWorker
from antarest.worker.archive_worker_service import run_archive_worker


def test_run_archive_worker__version(capsys):
    with pytest.raises(SystemExit) as ctx:
        run_archive_worker(["--version"])
    assert int(ctx.value.args[0]) == 0
    out, err = capsys.readouterr()
    assert __version__ in out


def test_run_archive_worker__help(capsys):
    with pytest.raises(SystemExit) as ctx:
        run_archive_worker(["--help"])
    assert int(ctx.value.args[0]) == 0
    out, err = capsys.readouterr()
    assert "CONFIG_FILE" in out
    assert "WORKSPACE" in out
    assert "LOCAL_ROOT" in out


WORKER_YAML = """\
storage:
  tmp_dir: /antarest_tmp_dir
  archive_dir: /studies/archives
  matrixstore: /matrixstore
  matrix_gc_dry_run: true
  workspaces:
    default:
      path: /studies/internal
    common_space:
      path: /mounts/common_spaces

logging:
  logfile: /path/to/worker.log
  json: false
  level: INFO

redis:
  host: redis-server
  port: 6379
  password: '*****'
"""


def test_run_archive_worker__logging_setup(tmp_path):
    """
    The purpose of this unit test is to check that the logging is set up correctly.
    """
    # create a `worker.yaml` with the right log path
    log_path = tmp_path.joinpath("worker.log")
    obj = yaml.safe_load(WORKER_YAML)
    obj["logging"]["logfile"] = str(log_path)
    config_path = tmp_path.joinpath("worker.yaml")
    with config_path.open(mode="w", encoding="utf-8") as fd:
        yaml.dump(obj, fd)

    # do not start the worker: use a Mock instead
    create_archive_worker = Mock()
    create_archive_worker.return_value = Mock(spec=ArchiveWorker)

    # noinspection SpellCheckingInspection
    with patch(
        "antarest.worker.archive_worker_service.create_archive_worker",
        new=create_archive_worker,
    ):
        run_archive_worker(
            [
                f"--config={config_path}",
                "--workspace=foo",
                "--local-root=/path/to/local/root",
            ]
        )

    # check: log file is generated with 2 messages
    assert log_path.is_file()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert "Starting Archive Worker" in lines[0]
    assert "Archive Worker task is done" in lines[1]
