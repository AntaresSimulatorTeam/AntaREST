import math
from unittest.mock import Mock

import pytest

from antarest.launcher.ssh_client import SlurmError, calculates_slurm_load, parse_cpu_load, parse_cpu_used


@pytest.mark.unit_test
def test_parse_cpu_used():
    assert parse_cpu_used("3/28/1/32") == 100 * 3 / (3 + 28)


@pytest.mark.unit_test
def test_parse_cpu_load():
    sinfo_output = "0.01     24    \n0.01   24  \nN/A     24    \n9.94   24 "
    assert math.isclose(
        parse_cpu_load(sinfo_output),
        100 * (0.01 + 0.01 + 9.94) / (24 + 24 + 24),
    )


@pytest.mark.unit_test
def test_calculates_slurm_load_whithout_pkey_fails():
    ssh_config = Mock()
    with pytest.raises(SlurmError):
        calculates_slurm_load(ssh_config, "fake_partition")
